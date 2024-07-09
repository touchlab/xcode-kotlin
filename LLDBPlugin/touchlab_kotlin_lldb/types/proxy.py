from typing import Optional, Union

import lldb

from ..util import evaluate
from .KonanNotInitializedObjectSyntheticProvider import KonanNotInitializedObjectSyntheticProvider
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from .KonanZerroSyntheticProvider import KonanZerroSyntheticProvider
from .base import get_type_info, obj_header_pointer, single_pointer
from .select_provider import select_provider


class KonanProxyTypeProvider:
    def __init__(self, valobj: lldb.SBValue, internal_dict):
        self._valobj = valobj
        self._proxy: Optional[Union[KonanBaseSyntheticProvider, KonanZerroSyntheticProvider]] = None

    def __getattr__(self, item):
        if self._proxy is None:
            cast_value = obj_header_pointer(self._valobj)
            type_info = get_type_info(cast_value)

            if not type_info:
                self._proxy = KonanNotInitializedObjectSyntheticProvider(self._valobj)
                return

            self._proxy = select_provider(cast_value, type_info)

        return getattr(self._proxy, item)


class KonanObjcProxyTypeProvider:
    def __init__(self, objc_obj: lldb.SBValue, internal_dict):
        self._objc_obj = objc_obj
        self._proxy: Optional[KonanProxyTypeProvider] = None

    def __getattr__(self, item):
        if self._proxy is None:
            objc_obj = single_pointer(self._objc_obj)

            konan_obj = evaluate(
                'void* __result = 0; (ObjHeader*)Kotlin_ObjCExport_refFromObjC((void*){:#x}, &__result)',
                objc_obj.unsigned
            )
            self._proxy = KonanProxyTypeProvider(konan_obj, {})
        return getattr(self._proxy, item)
