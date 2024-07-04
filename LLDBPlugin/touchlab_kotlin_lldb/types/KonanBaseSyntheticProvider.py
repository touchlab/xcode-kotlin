import lldb
from lldb import SBSyntheticValueProvider, SBValue, SBError

from ..util import log, DebuggerException, kotlin_object_to_string, evaluate


class KonanBaseSyntheticProvider(object):
    def __init__(self, valobj: SBValue):
        super().__init__()

        self._valobj = valobj
        self._process = lldb.debugger.GetSelectedTarget().GetProcess()

    def evaluate_children_count(self):
        return evaluate('(__konan_safe_int_t)Konan_DebugGetFieldCount({:#x})', self._valobj.unsigned).signed

    def evaluate_field_address(self, index):
        return evaluate(
            '(__konan_safe_void_t*)Konan_DebugGetFieldAddress({:#x}, {})',
            self._valobj.unsigned,
            index,
        ).unsigned

    def evaluate_field_type(self, index):
        return evaluate(
            '(__konan_safe_int_t)Konan_DebugGetFieldType({:#x}, {})',
            self._valobj.unsigned,
            index,
        ).unsigned

    def evaluate_field_name(self, index):
        error = SBError()
        name = self._process.ReadCStringFromMemory(
            evaluate(
                '(__konan_safe_char_t *)Konan_DebugGetFieldName({:#x}, (__konan_safe_int_t){})',
                self._valobj.unsigned,
                index,
            ).unsigned,
            0x1000,
            error,
        )
        if not error.Success():
            raise DebuggerException(
                'Could not read field name at index {} (error: {})'.format(index, error.description)
            )
        return name

    def read_cstring(self, expression: str, *args, **kwargs) -> str:
        error = SBError()
        result = self._process.ReadCStringFromMemory(
            evaluate(expression, *args, **kwargs).unsigned,
            0x1000,
            error,
        )
        if not error.Success():
            raise DebuggerException(
                'Could not read cstring returned from {} (error: {})'.format(
                    expression.format(*args, **kwargs),
                    error.description,
                )
            )
        return result

    def to_string(self):
        return kotlin_object_to_string(self._process, self._valobj.unsigned)