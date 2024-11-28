import os
from typing import Optional

import lldb

from .stepping.KonanHook import KonanHook
from .types.base import KOTLIN_CATEGORY, KOTLIN_OBJ_HEADER_TYPE, KOTLIN_ARRAY_HEADER_TYPE
from .util.log import log
from .commands import FieldTypeCommand, SymbolByNameCommand, TypeByAddressCommand, GCCollectCommand

from .types.summary import kotlin_object_type_summary, kotlin_objc_class_summary
from .types.proxy import KonanProxyTypeProvider, KonanObjcProxyTypeProvider

from .cache import LLDBCache

os.environ['CLIENT_TYPE'] = 'Xcode'

KONAN_INIT_PREFIX = '_Konan_init_'
KONAN_INIT_MODULE_NAME = '[0-9a-zA-Z_]+'
KONAN_INIT_SUFFIX = '_kexe'

def __lldb_init_module(debugger: lldb.SBDebugger, _):
    log(lambda: "init start")

    reset_cache()
    configure_types(debugger)
    register_commands(debugger)
    register_hooks(debugger)

    configure_objc_types_init(debugger)

    log(lambda: "init end")


def reset_cache():
    """Xcode reuses LLDB between program runs, so we need to clear any symbol references we made as they are no
    longer valid."""
    LLDBCache.reset()


def configure_objc_types_init(debugger: lldb.SBDebugger):
    target = debugger.GetDummyTarget()
    breakpoint = target.BreakpointCreateByRegex(
        "^{}({})({})?$".format(KONAN_INIT_PREFIX, KONAN_INIT_MODULE_NAME, KONAN_INIT_SUFFIX)
    )
    breakpoint.SetOneShot(True)
    breakpoint.SetAutoContinue(True)
    breakpoint.SetScriptCallbackFunction('{}.{}'.format(__name__, configure_objc_types_breakpoint.__name__))


def configure_objc_types_breakpoint(frame: lldb.SBFrame, bp_loc: lldb.SBBreakpointLocation, internal_dict):
    process = frame.thread.process
    target = process.target

    symbols = target.FindSymbols('_OBJC_CLASS_RO_$_KotlinBase')

    base_class_name: Optional[str] = None
    for symbol_context in symbols:
        error = lldb.SBError()
        name_addr = process.ReadPointerFromMemory(symbol_context.symbol.addr.GetLoadAddress(target) + 6 * 4, error)
        # TODO: Log error?
        if not error.success:
            continue
        base_class_name = process.ReadCStringFromMemory(name_addr, 128, error)
        # TODO: Log error?
        if not error.success:
            continue

        break

    module_name = frame.symbol.name.removeprefix(KONAN_INIT_PREFIX).removesuffix(KONAN_INIT_SUFFIX)
    if module_name == "stdlib":
        return False

    specifiers_to_register = [
        lldb.SBTypeNameSpecifier(
            '^{}\\.'.format(module_name),
            lldb.eMatchTypeRegex,
        ),
    ]

    if base_class_name is not None:
        objc_class_prefix = base_class_name.removesuffix("Base")
        specifiers_to_register.append(
            lldb.SBTypeNameSpecifier(
                '^{}'.format(objc_class_prefix),
                lldb.eMatchTypeRegex,
            )
        )

    category = target.debugger.GetCategory(KOTLIN_CATEGORY)

    for type_specifier in specifiers_to_register:
        category.AddTypeSummary(
            type_specifier,
            lldb.SBTypeSummary.CreateWithFunctionName(
                '{}.{}'.format(__name__, kotlin_objc_class_summary.__name__),
                lldb.eTypeOptionHideValue,
            )
        )
        category.AddTypeSynthetic(
            type_specifier,
            lldb.SBTypeSynthetic.CreateWithClassName(
                '{}.{}'.format(__name__, KonanObjcProxyTypeProvider.__name__),
            )
        )

    bp_loc.GetBreakpoint().SetEnabled(False)

    return False


def configure_types(debugger: lldb.SBDebugger):
    category = debugger.CreateCategory(KOTLIN_CATEGORY)

    types_to_register = [
        KOTLIN_OBJ_HEADER_TYPE,
        KOTLIN_ARRAY_HEADER_TYPE,
    ]

    for type_to_register in types_to_register:
        category.AddTypeSummary(
            type_to_register,
            lldb.SBTypeSummary.CreateWithFunctionName(
                '{}.{}'.format(__name__, kotlin_object_type_summary.__name__),
                lldb.eTypeOptionHideValue
            )
        )
        category.AddTypeSynthetic(
            type_to_register,
            lldb.SBTypeSynthetic.CreateWithClassName(
                '{}.{}'.format(__name__, KonanProxyTypeProvider.__name__),
            )
        )

    category.SetEnabled(True)


def register_commands(debugger: lldb.SBDebugger):
    commands_to_register = [
        FieldTypeCommand,
        SymbolByNameCommand,
        TypeByAddressCommand,
        GCCollectCommand,
    ]

    for command in commands_to_register:
        debugger.HandleCommand(
            'command script add -c {}.{} {}'.format(__name__, command.__name__, command.program)
        )


def register_hooks(debugger: lldb.SBDebugger):
    # Avoid Kotlin/Native runtime
    debugger.HandleCommand('settings set target.process.thread.step-avoid-regexp ^::Kotlin_')

    hooks_to_register = [
        KonanHook,
    ]

    for hook in hooks_to_register:
        debugger.HandleCommand('target stop-hook add -P {}.{}'.format(__name__, hook.__name__))
