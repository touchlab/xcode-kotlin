import lldb
from .KonanNotInitializedObjectSyntheticProvider import KonanNotInitializedObjectSyntheticProvider
from .KonanNullSyntheticProvider import KonanNullSyntheticProvider
from .base import get_type_info, obj_header_type
from .select_provider import select_provider


class KonanProxyTypeProvider:
    def __init__(self, valobj: lldb.SBValue, internal_dict):
        if valobj.unsigned == 0:
            self._proxy = KonanNullSyntheticProvider(valobj)
            return

        cast_value = valobj.GetNonSyntheticValue().Cast(obj_header_type())
        type_info = get_type_info(cast_value)
        if not type_info:
            self._proxy = KonanNotInitializedObjectSyntheticProvider(valobj)
            return
        self._proxy = select_provider(cast_value, type_info)

    def __getattr__(self, item):
        return getattr(self._proxy, item)
