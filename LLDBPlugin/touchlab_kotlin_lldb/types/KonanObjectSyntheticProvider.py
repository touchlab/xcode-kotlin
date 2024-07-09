import lldb


from .base import _TYPE_CONVERSION, type_info_type
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider


class KonanObjectSyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        self._children_count = 0
        self._children_names = []
        self._was_updated = False

        super().__init__(valobj, type_info)

    def update(self) -> bool:
        self._was_updated = True
        self._children_count = int(self._type_info.extendedInfo_.fieldsCount_)
        if self._children_count < 0:
            self._children_count = 0
        if self._children_count > 0:
            field_names = self._type_info.extendedInfo_.fieldNames_
            self._children_names = [
                self.read_cstring(int(field_names[i])) for i in range(self._children_count)
            ]
        return False

    def num_children(self):
        return self._children_count

    def has_children(self):
        return True

    def get_child_index(self, name):
        # if self._children is None:
        return self._children_names.index(name)

    def get_child_at_index(self, index):
        value_type = self._type_info.extendedInfo_.fieldTypes_[index]
        address = self.get_child_address_at_index(index)
        return _TYPE_CONVERSION[int(value_type)](self, self._valobj, address, self._children_names[index])

    def get_child_address_at_index(self, index):
        return self._valobj.unsigned + int(self._type_info.extendedInfo_.fieldOffsets_[index])
