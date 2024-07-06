import lldb

from .base import get_type_info
from ..util import log, DebuggerException
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider


class KonanListSyntheticProvider(KonanBaseSyntheticProvider):
    __possible_backing_properties = {'backing', '$this_asList', 'backingArray'}

    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        super().__init__(valobj, type_info)

        real_children_count = int(self._type_info.extendedInfo_.fieldsCount_)
        field_names = self._type_info.extendedInfo_.fieldNames_

        for i in range(real_children_count):
            name = self.read_cstring(int(field_names[i]))
            if name in KonanListSyntheticProvider.__possible_backing_properties:
                address = self._valobj.unsigned + int(self._type_info.extendedInfo_.fieldOffsets_[i])
                backing_value = self._valobj.CreateValueFromAddress(
                    name,
                    address,
                    self._valobj.type,
                )
                child_type_info = get_type_info(backing_value)
                if child_type_info is None:
                    continue
                self._backing = KonanArraySyntheticProvider(backing_value, child_type_info)
                return

        raise DebuggerException(
            "Couldn't find backing for list {:#x}, name: {}".format(self._valobj.unsigned, self._valobj.name)
        )

    def update(self):
        super().update()

        self._backing.update()
        return True

    def num_children(self):
        return self._backing.num_children()

    def has_children(self):
        return self._backing.has_children()

    def get_child_index(self, name):
        return self._backing.get_child_index(name)

    def get_child_at_index(self, index):
        return self._backing.get_child_at_index(index)

    def to_string(self):
        return self._backing.to_string()
