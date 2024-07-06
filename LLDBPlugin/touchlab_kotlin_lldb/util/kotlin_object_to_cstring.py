from typing import Optional

from lldb import SBProcess, SBError

from .DebuggerException import DebuggerException
from .expression import evaluate
from .log import log
from ..cache import LLDBCache


def get_debug_buffer_addr() -> int:
    self = LLDBCache.instance()
    if self._debug_buffer_addr is None:
        self._debug_buffer_addr = int(evaluate("(__konan_safe_void_t *)Konan_DebugBuffer()").unsigned)
    return self._debug_buffer_addr


def get_debug_buffer_size() -> int:
    self = LLDBCache.instance()
    if self._debug_buffer_size is None:
        self._debug_buffer_size = int(evaluate("(__konan_safe_int_t)Konan_DebugBufferSize()").unsigned)
    return self._debug_buffer_size


def kotlin_object_to_string(process: SBProcess, object_addr: int) -> Optional[str]:
    debug_buffer_addr = get_debug_buffer_addr()
    debug_buffer_size = get_debug_buffer_size()
    string_len = evaluate(
        '(__konan_safe_int_t)Konan_DebugObjectToUtf8Array((__konan_safe_void_t*){:#x}, (__konan_safe_void_t *){:#x}, {});',
        object_addr,
        debug_buffer_addr,
        debug_buffer_size,
    ).signed

    if not string_len:
        return None

    error = SBError()
    s = process.ReadCStringFromMemory(debug_buffer_addr, int(string_len), error)
    if not error.Success():
        raise DebuggerException("Couldn't read object description Error: {}.".format(error.description))
    return s
