from lldb import SBDebugger, SBValue, SBTypeCategory, SBTypeSynthetic

from .base import type_info
from .KonanNotInitializedObjectSyntheticProvider import KonanNotInitializedObjectSyntheticProvider
from .KonanNullSyntheticProvider import KonanNullSyntheticProvider
from .select_provider import select_provider


class KonanProxyTypeProvider:
    def __init__(self, valobj: SBValue, internal_dict):
        if valobj.unsigned == 0:
            self._proxy = KonanNullSyntheticProvider(valobj)
            return

        tip = type_info(valobj)
        if not tip:
            self._proxy = KonanNotInitializedObjectSyntheticProvider(valobj)
            return
        self._proxy = select_provider(valobj)

    def __getattr__(self, item):
        return getattr(self._proxy, item)


