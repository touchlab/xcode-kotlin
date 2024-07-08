import lldb

from ..util import evaluate
from .KonanNotInitializedObjectSyntheticProvider import KonanNotInitializedObjectSyntheticProvider
from .KonanNullSyntheticProvider import KonanNullSyntheticProvider
from .base import get_type_info, obj_header_type
from .select_provider import select_provider


class KonanObjcProxyTypeProvider:
    def __init__(self, valobj: lldb.SBValue, internal_dict):
        if valobj.unsigned == 0:
            self._proxy = KonanNullSyntheticProvider(valobj)
            return

        obj = evaluate(
            'void* __result = 0; (ObjHeader*)Kotlin_ObjCExport_refFromObjC((void*){:#x}, &__result)',
            valobj.unsigned
        )
        self._proxy = KonanProxyTypeProvider(obj, internal_dict)

    def __getattr__(self, item):
        return getattr(self._proxy, item)


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
