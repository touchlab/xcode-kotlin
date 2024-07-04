import lldb
from lldb import SBExpressionOptions, SBValue
from .log import log
from ..cache import LLDBCache


def initialize_expression_options():
    options = SBExpressionOptions()
    options.SetIgnoreBreakpoints(True)
    options.SetAutoApplyFixIts(False)
    options.SetFetchDynamicValue(False)
    options.SetGenerateDebugInfo(False)
    options.SetSuppressPersistentResult(True)
    options.SetREPLMode(False)
    return options


def initialize_top_level_expression_options():
    options = initialize_expression_options()
    options.SetTopLevel(True)
    options.SetSuppressPersistentResult(False)
    return options


EXPRESSION_OPTIONS = initialize_expression_options()
TOP_LEVEL_EXPRESSION_OPTIONS = initialize_top_level_expression_options()


def evaluate(expression: str, *args, **kwargs):
    declare_helper_types()
    formatted_expression = expression.format(*args, **kwargs)
    result = lldb.debugger.GetSelectedTarget().EvaluateExpression(formatted_expression, EXPRESSION_OPTIONS)
    log(lambda: "evaluate: {} => {}".format(formatted_expression, result))
    return result


def top_level_evaluate(expr):
    log(lambda: "top_level_evaluate: target={}".format(lldb.debugger.GetSelectedTarget()))
    result = lldb.debugger.GetSelectedTarget().EvaluateExpression(expr, TOP_LEVEL_EXPRESSION_OPTIONS)
    log(lambda: "top_level_evaluate: {} => {}".format(expr, result))
    return result


def declare_helper_types():
    self = LLDBCache.instance()
    if not self._helper_types_declared:
        top_level_evaluate(
            'typedef void __konan_safe_void_t;'
            'typedef int __konan_safe_int_t;'
            'typedef char __konan_safe_char_t;'
            'typedef bool __konan_safe_bool_t;'
            'typedef float __konan_safe_float_t;'
            'typedef double __konan_safe_double_t;'
            'typedef void ObjHeader;'
            'typedef struct MapEntry { ObjHeader* key; ObjHeader* value; } MapEntry;'
        )
        self._helper_types_declared = True
