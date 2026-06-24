import re
from typing import List, Optional

import lldb

from .types.base import KOTLIN_CATEGORY
from .types.summary import kotlin_objc_class_summary
from .types.proxy import KonanObjcProxyTypeProvider
from .cache import LLDBCache
from .util.log import log

# `_Konan_init_MyMod` (framework) or `_Konan_init_MyApp_kexe` (executable); group 1 = module name.
_KONAN_INIT_RE = re.compile(r'^_Konan_init_([0-9a-zA-Z_]+?)(_kexe)?$')
_KOTLIN_RUNTIME_MARKER = 'Kotlin_initRuntimeIfNeeded'
_KOTLIN_BASE_OBJC_SYMBOL = '_OBJC_CLASS_RO_$_KotlinBase'
# `name` pointer offset in the 64-bit ObjC class_ro_t; all current Apple targets are 64-bit.
_OBJC_CLASS_RO_NAME_OFFSET = 6 * 4
# Skipping these by PATH ALONE — before any symbol API realizes their symtab — is the launch-time win.
_SYSTEM_PATH_MARKERS = ('/usr/lib', '/System/')
# Cap ObjC-prefix retries: the read fails until dyld rebases the class_ro_t name pointer.
_MAX_PREFIX_ATTEMPTS = 16


def _module_key(module: lldb.SBModule) -> str:
    # Fall back to path so two no-UUID modules don't collide on one key.
    return module.GetUUIDString() or module.GetFileSpec().fullpath or ''


def _is_candidate_module(module: lldb.SBModule) -> bool:
    directory = module.GetFileSpec().GetDirectory() or ''
    return not any(marker in directory for marker in _SYSTEM_PATH_MARKERS)


def _is_kotlin_module(module: lldb.SBModule) -> bool:
    return len(module.FindSymbols(_KOTLIN_RUNTIME_MARKER)) > 0


def _kotlin_module_names(module: lldb.SBModule) -> List[str]:
    names: List[str] = []
    for symbol in module.symbols:
        match = _KONAN_INIT_RE.match(symbol.name or '')
        if match is None:
            continue
        module_name = match.group(1)
        if module_name == 'stdlib':
            continue
        names.append(module_name)
    return names


def _read_objc_class_prefix(
    target: lldb.SBTarget,
    process: lldb.SBProcess,
    base_symbols: lldb.SBSymbolContextList,
) -> Optional[str]:
    for symbol_context in base_symbols:
        error = lldb.SBError()
        symbol_addr = symbol_context.symbol.addr.GetLoadAddress(target)
        name_addr = process.ReadPointerFromMemory(symbol_addr + _OBJC_CLASS_RO_NAME_OFFSET, error)
        if not error.success:
            continue
        base_class_name = process.ReadCStringFromMemory(name_addr, 128, error)
        if not error.success or not base_class_name:
            continue
        # `or None`: an empty prefix would build `^`, matching every type.
        return base_class_name.removesuffix('Base') or None
    return None


def _register_specifiers(target: lldb.SBTarget, specifiers: List[lldb.SBTypeNameSpecifier]):
    category = target.debugger.GetCategory(KOTLIN_CATEGORY)
    for type_specifier in specifiers:
        category.AddTypeSummary(
            type_specifier,
            lldb.SBTypeSummary.CreateWithFunctionName(
                '{}.{}'.format(kotlin_objc_class_summary.__module__, kotlin_objc_class_summary.__name__),
                lldb.eTypeOptionHideValue,
            ),
        )
        category.AddTypeSynthetic(
            type_specifier,
            lldb.SBTypeSynthetic.CreateWithClassName(
                '{}.{}'.format(KonanObjcProxyTypeProvider.__module__, KonanObjcProxyTypeProvider.__name__),
            ),
        )


def _try_register_objc_prefix(
    target: lldb.SBTarget,
    process: lldb.SBProcess,
    cache: 'LLDBCache',
    module: lldb.SBModule,
    key: str,
) -> bool:
    """Register `^<prefix>`. True when handled (registered / no base class / cap hit), False to retry."""
    base_symbols = module.FindSymbols(_KOTLIN_BASE_OBJC_SYMBOL)
    if not base_symbols:
        return True  # no exported ObjC base class; module-name formatters suffice

    prefix = _read_objc_class_prefix(target, process, base_symbols)
    if prefix:
        _register_specifiers(target, [lldb.SBTypeNameSpecifier('^{}'.format(prefix), lldb.eMatchTypeRegex)])
        log(lambda: 'Registered ObjC prefix ^{} for {}.'.format(prefix, module.GetFileSpec().GetFilename()))
        return True

    attempts = cache.pending_prefix.get(key, 0) + 1
    cache.pending_prefix[key] = attempts
    if attempts >= _MAX_PREFIX_ATTEMPTS:
        log(lambda: 'Gave up reading ObjC prefix for {} after {} stops; '
            '^<prefix> formatting unavailable.'.format(module.GetFileSpec().GetFilename(), attempts))
        return True
    return False


def _register_kotlin_module(
    target: lldb.SBTarget,
    process: lldb.SBProcess,
    cache: 'LLDBCache',
    module: lldb.SBModule,
    key: str,
) -> bool:
    """First sight of a Kotlin module: register `^<module>\\.` now, then attempt the ObjC prefix."""
    names = _kotlin_module_names(module)
    if not names:
        log(lambda: 'Kotlin marker present but no module names for {}; skipping.'.format(
            module.GetFileSpec().GetFilename()))
        return True
    _register_specifiers(target, [
        lldb.SBTypeNameSpecifier('^{}\\.'.format(name), lldb.eMatchTypeRegex) for name in names
    ])
    return _try_register_objc_prefix(target, process, cache, module, key)


def scan_and_register_modules(execution_context: lldb.SBExecutionContext):
    """Lazily register Kotlin formatters at stop time. Replaces the old global `_Konan_init_*`
    regex breakpoint that realized every module's symtab at launch. Side effect only — never
    influences whether the process stops."""
    target = execution_context.target
    if not target.IsValid():
        return
    process = target.GetProcess()
    if not process.IsValid():
        return

    cache = LLDBCache.instance()
    for i in range(target.GetNumModules()):
        module = target.GetModuleAtIndex(i)
        key = _module_key(module)

        if key in cache.registered_module_keys:
            continue

        if key in cache.pending_prefix:  # known Kotlin module, prefix still settling
            if _try_register_objc_prefix(target, process, cache, module, key):
                cache.pending_prefix.pop(key, None)
                cache.registered_module_keys.add(key)
            continue

        if not _is_candidate_module(module) or not _is_kotlin_module(module):
            cache.registered_module_keys.add(key)
            continue

        if _register_kotlin_module(target, process, cache, module, key):
            cache.pending_prefix.pop(key, None)
            cache.registered_module_keys.add(key)
