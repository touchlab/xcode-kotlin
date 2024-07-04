import os

from lldb import SBDebugger, SBTypeCategory, SBTypeSummary, eTypeOptionHideValue, SBTypeSynthetic

from .stepping.KonanHook import KonanHook
from .types import KOTLIN_CATEGORY, KOTLIN_NATIVE_TYPE_SPECIFIER
from .util.log import log
from .util.expression import top_level_evaluate
from .commands import FieldTypeCommand, SymbolByNameCommand, TypeByAddressCommand

from .types import kotlin_object_type_summary, KonanProxyTypeProvider

from .cache import LLDBCache

os.environ['CLIENT_TYPE'] = 'Xcode'


def __lldb_init_module(debugger: SBDebugger, _):
    log(lambda: "init start")

    reset_cache()
    configure_types(debugger)
    register_commands(debugger)
    register_hooks(debugger)

    log(lambda: "init end")


def reset_cache():
    """Xcode reuses LLDB between program runs, so we need to clear any symbol references we made as they are no
    longer valid."""
    LLDBCache.reset()


def configure_types(debugger: SBDebugger):
    category: SBTypeCategory = debugger.CreateCategory(KOTLIN_CATEGORY)
    category.AddTypeSummary(
        KOTLIN_NATIVE_TYPE_SPECIFIER,
        SBTypeSummary.CreateWithFunctionName(
            '{}.{}'.format(__name__, kotlin_object_type_summary.__name__),
            eTypeOptionHideValue
        )
    )
    category.AddTypeSynthetic(
        KOTLIN_NATIVE_TYPE_SPECIFIER,
        SBTypeSynthetic.CreateWithClassName(
            '{}.{}'.format(__name__, KonanProxyTypeProvider.__name__),
        )
    )

    # noinspection PyArgumentList
    category.SetEnabled(True)


def register_commands(debugger: SBDebugger):
    commands_to_register = [
        FieldTypeCommand,
        SymbolByNameCommand,
        TypeByAddressCommand,
    ]

    for command in commands_to_register:
        debugger.HandleCommand(
            'command script add -c {}.{} {}'.format(__name__, command.__name__, command.program)
        )


def register_hooks(debugger: SBDebugger):
    # Avoid Kotlin/Native runtime
    debugger.HandleCommand('settings set target.process.thread.step-avoid-regexp ^::Kotlin_')

    hooks_to_register = [
        KonanHook,
    ]

    for hook in hooks_to_register:
        debugger.HandleCommand('target stop-hook add -P {}.{}'.format(__name__, hook.__name__))
