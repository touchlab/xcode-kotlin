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
    options.SetLanguage(lldb.eLanguageTypeC)
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
        options = initialize_top_level_expression_options()
        options.SetLanguage(lldb.eLanguageTypeC_plus_plus_20)
        result = lldb.debugger.GetSelectedTarget().EvaluateExpression(
            '#include "{}/konan_debug.h"'.format(script_dir),
            options
        )
        log(lambda: '{}'.format(result))
        # top_level_evaluate(
        #     ,
        #     # 'typedef void __konan_safe_void_t;'
        #     # 'typedef int __konan_safe_int_t;'
        #     # 'typedef char __konan_safe_char_t;'
        #     # 'typedef bool __konan_safe_bool_t;'
        #     # 'typedef float __konan_safe_float_t;'
        #     # 'typedef double __konan_safe_double_t;'
        #     # 'typedef void ObjHeader;'
        #     # 'typedef struct MapEntry { ObjHeader* key; ObjHeader* value; } MapEntry;\n'
        #     # '''
        #     # typedef struct Konan_ObjectField { void* address; int type; char* name; } Konan_ObjectField;
        #     # typedef struct Konan_ObjectFieldList { int count; Konan_ObjectField* fields; } Konan_ObjectFieldList;
        #     # Konan_ObjectFieldList Konan_GetObjectFields(ObjHeader* object) {
        #     #     int field_count = (int)Konan_DebugGetFieldCount(object);
        #     #     Konan_ObjectField* fields = (Konan_ObjectField*)malloc(field_count * sizeof(Konan_ObjectField));
        #     #     for (int i = 0; i < field_count; i++) {
        #     #         void* address = (void*)Konan_DebugGetFieldAddress(object, i);
        #     #         int type = (int)Konan_DebugGetFieldType(object, i);
        #     #         char* name = (char*)Konan_DebugGetFieldName(object, i);
        #     #
        #     #         fields[i] = (Konan_ObjectField){
        #     #             address, type, name
        #     #         };
        #     #     }
        #     #     return (Konan_ObjectFieldList){
        #     #         field_count, fields
        #     #     };
        #     # }
        #     # '''
        # )
        self._helper_types_declared = True
