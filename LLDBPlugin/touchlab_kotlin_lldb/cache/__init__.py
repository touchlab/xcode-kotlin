from typing import Optional

import lldb

__lldb_cache_instance: 'LLDBCache'


class LLDBCache:
    @classmethod
    def reset(cls):
        global __lldb_cache_instance
        __lldb_cache_instance = LLDBCache()

    @classmethod
    def instance(cls):
        global __lldb_cache_instance
        return __lldb_cache_instance

    def __init__(self):
        self._debug_buffer_addr: Optional[int] = None
        self._debug_buffer_size: Optional[int] = None
        self._string_symbol_value: Optional[lldb.value] = None
        self._list_symbol_value: Optional[lldb.value] = None
        self._map_symbol_value: Optional[lldb.value] = None
        self._helper_types_declared: bool = False
        self._type_info_type: Optional[lldb.SBType] = None
        self._obj_header_type: Optional[lldb.SBType] = None
        self._array_header_type: Optional[lldb.SBType] = None
        self._runtime_type_size: Optional[lldb.value] = None
        self._runtime_type_alignment: Optional[lldb.value] = None
