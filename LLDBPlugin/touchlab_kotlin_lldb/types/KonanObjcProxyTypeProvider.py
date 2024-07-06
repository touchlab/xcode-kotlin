import lldb

from .KonanNullSyntheticProvider import KonanNullSyntheticProvider
from .KonanProxyTypeProvider import KonanProxyTypeProvider
from ..util import evaluate


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
