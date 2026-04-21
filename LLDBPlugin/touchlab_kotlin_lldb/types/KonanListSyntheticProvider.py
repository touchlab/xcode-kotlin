from typing import Optional

import lldb

from .base import get_type_info
from ..util import log, DebuggerException
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider


class KonanListSyntheticProvider(KonanObjectSyntheticProvider):
    __possible_backing_properties = {'backing', '$this_asList', 'backingArray'}
    __possible_size_properties = {'length'}

    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        self._backing: KonanArraySyntheticProvider = None  # type: ignore
        self._size: Optional[int] = None

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
        self._size = self._try_update_size()
        return False

    def num_children(self):
        if self._size is None:
            return self._backing.num_children()
        else:
            return self._size

    def has_children(self):
        return True

    def get_child_index(self, name):
        return self._backing.get_child_index(name)

    def get_child_at_index(self, index):
        return self._backing.get_child_at_index(index)

    def to_string(self):
        if self._size is None:
            return self._backing.to_string()
        elif self._size == 1:
            return '1 value'
        else:
            return '{} values'.format(self._size)

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

    def _try_update_size(self) -> Optional[int]:
        for index, name in enumerate(self._children_names):
            if name not in KonanListSyntheticProvider.__possible_size_properties:
                continue
            try:
                value = super().get_child_at_index(index)
                if value is None or not value.IsValid():
                    continue
                size = value.GetValueAsSigned()
                if size < 0:
                    continue
                return int(size)
            except BaseException:
                continue
        return None
