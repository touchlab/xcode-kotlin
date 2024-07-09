from typing import Optional

import lldb

from .base import get_type_info
from ..util import log, DebuggerException
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider


class KonanListSyntheticProvider(KonanObjectSyntheticProvider):
    __possible_backing_properties = {'backing', '$this_asList', 'backingArray'}

    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        self._backing: KonanArraySyntheticProvider = None  # type: ignore

        super().__init__(valobj, type_info)

    def update(self):
        super().update()

        if self._backing is None:
            backing: Optional[KonanArraySyntheticProvider] = None
            for index, name in enumerate(self._children_names):
                if name in KonanListSyntheticProvider.__possible_backing_properties:
                    backing = self._create_backing(index, name)
                    if backing is not None:
                        break

            if backing is None:
                raise DebuggerException(
                    "Couldn't find backing for list {:#x}, name: {}".format(self._valobj.unsigned, self._valobj.name)
                )

            self._backing = backing

        self._backing.update()
        return False

    def num_children(self):
        return self._backing.num_children()

    def has_children(self):
        return True

    def get_child_index(self, name):
        return self._backing.get_child_index(name)

    def get_child_at_index(self, index):
        return self._backing.get_child_at_index(index)

    def to_string(self):
        return self._backing.to_string()

    def _create_backing(self, index: int, name: str) -> Optional[KonanArraySyntheticProvider]:
        address = self.get_child_address_at_index(index)
        backing_value = self._valobj.CreateValueFromAddress(
            name,
            address,
            self._valobj.type,
        )
        child_type_info = get_type_info(backing_value)
        if child_type_info is None:
            return None
        else:
            return KonanArraySyntheticProvider(backing_value, child_type_info)
