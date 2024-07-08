import re

from lldb import SBDebugger, SBExecutionContext, SBCommandReturnObject

from ..types.summary import kotlin_object_type_summary
from ..util.expression import evaluate


__KONAN_VARIABLE = re.compile('kvar:(.*)#internal')
__KONAN_VARIABLE_TYPE = re.compile('^kfun:<get-(.*)>\\(\\)(.*)$')
__TYPES_KONAN_TO_C = {
   'kotlin.Byte': ('int8_t', lambda v: v.signed),
   'kotlin.Short': ('short', lambda v: v.signed),
   'kotlin.Int': ('int', lambda v: v.signed),
   'kotlin.Long': ('long', lambda v: v.signed),
   'kotlin.UByte': ('int8_t', lambda v: v.unsigned),
   'kotlin.UShort': ('short', lambda v: v.unsigned),
   'kotlin.UInt': ('int', lambda v: v.unsigned),
   'kotlin.ULong': ('long', lambda v: v.unsigned),
   'kotlin.Char': ('short', lambda v: v.signed),
   'kotlin.Boolean': ('bool', lambda v: v.signed),
   'kotlin.Float': ('float', lambda v: v.value),
   'kotlin.Double': ('double', lambda v: v.value)
}


class KonanGlobalsCommand:
    program = 'konan_globals'

    def __init__(self, debugger, unused):
        pass

    def __call__(
            self,
            debugger: SBDebugger,
            command,
            exe_ctx: SBExecutionContext,
            result: SBCommandReturnObject,
    ):
        global __KONAN_VARIABLE, __KONAN_VARIABLE_TYPE, __TYPES_KONAN_TO_C
        target = debugger.GetSelectedTarget()
        process = target.GetProcess()
        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame()

        konan_variable_symbols = list(filter(lambda v: __KONAN_VARIABLE.match(v.name), frame.GetModule().symbols))
        visited = list()
        for symbol in konan_variable_symbols:
            name = __KONAN_VARIABLE.search(symbol.name).group(1)

            if name in visited:
                continue
            visited.append(name)

            getters = list(
                filter(lambda v: re.match('^kfun:<get-{}>\\(\\).*$'.format(name), v.name), frame.module.symbols))
            if not getters:
                result.AppendMessage("storage not found for name:{}".format(name))
                continue

            getter_functions = frame.module.FindFunctions(getters[0].name)
            if not getter_functions:
                continue

            address = getter_functions[0].function.GetStartAddress().GetLoadAddress(target)
            type = __KONAN_VARIABLE_TYPE.search(getters[0].name).group(2)
            (c_type, extractor) = __TYPES_KONAN_TO_C[type] if type in __TYPES_KONAN_TO_C.keys() else ('ObjHeader *', lambda v: kotlin_object_type_summary(v))
            value = evaluate('(({0} (*)()){1:#x})()', c_type, address)
            str_value = extractor(value)
            result.AppendMessage('{} {}: {}'.format(type, name, str_value))
