import lldb
from .log import log
from ..cache import LLDBCache


def initialize_expression_options():
    options = lldb.SBExpressionOptions()
    options.SetIgnoreBreakpoints(True)
    options.SetAutoApplyFixIts(False)
    options.SetFetchDynamicValue(False)
    options.SetGenerateDebugInfo(False)
    options.SetSuppressPersistentResult(True)
    options.SetREPLMode(False)
    options.SetAllowJIT(True)
    options.SetLanguage(lldb.eLanguageTypeC_plus_plus_20)
    return options


def initialize_top_level_expression_options():
    options = initialize_expression_options()
    options.SetTopLevel(True)
    options.SetSuppressPersistentResult(False)
    return options


EXPRESSION_OPTIONS = initialize_expression_options()
TOP_LEVEL_EXPRESSION_OPTIONS = initialize_top_level_expression_options()


def evaluate(expression: str, *args, **kwargs) -> lldb.SBValue:
    declare_helper_types()
    formatted_expression = expression.format(*args, **kwargs)
    result = lldb.debugger.GetSelectedTarget().EvaluateExpression(formatted_expression, EXPRESSION_OPTIONS)
    log(lambda: "evaluate: {} => {}".format(formatted_expression, result))
    return result


def top_level_evaluate(expr) -> lldb.SBValue:
    log(lambda: "top_level_evaluate: target={}".format(lldb.debugger.GetSelectedTarget()))
    result = lldb.debugger.GetSelectedTarget().EvaluateExpression(expr, TOP_LEVEL_EXPRESSION_OPTIONS)
    log(lambda: "top_level_evaluate: {} => {}".format(expr, result))
    return result


def declare_helper_types():
    self = LLDBCache.instance()
    if not self._helper_types_declared:
        import pathlib
        script_dir = pathlib.Path(__file__).parent.resolve()
        expression = '#include "{}/konan_debug.h"'.format(script_dir)
        result = top_level_evaluate(expression)
        log(lambda: '{} => {}'.format(expression, result))

        self._helper_types_declared = True
