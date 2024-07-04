__lldb_cache_instance = None


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
        self._debug_buffer_addr = None
        self._debug_buffer_size = None
        self._string_symbol_addr = None
        self._list_symbol_addr = None
        self._map_symbol_addr = None
        self._helper_types_declared = False
