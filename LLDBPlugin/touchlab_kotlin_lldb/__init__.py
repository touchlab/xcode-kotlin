import os

import lldb

from .stepping.KonanHook import KonanHook
from .types.base import KOTLIN_CATEGORY, KOTLIN_OBJ_HEADER_TYPE, KOTLIN_ARRAY_HEADER_TYPE
from .util.log import log
from .commands import FieldTypeCommand, SymbolByNameCommand, TypeByAddressCommand, GCCollectCommand

from .types.summary import kotlin_object_type_summary
from .types.proxy import KonanProxyTypeProvider

from .cache import LLDBCache

os.environ['CLIENT_TYPE'] = 'Xcode'


def __lldb_init_module(debugger: lldb.SBDebugger, _):
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

    debugger.HandleCommand('target stop-hook add -P {}.{}'.format(__name__, KonanHook.__name__))
