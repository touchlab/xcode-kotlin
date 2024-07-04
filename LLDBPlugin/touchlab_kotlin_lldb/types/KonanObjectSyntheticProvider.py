import lldb
from lldb import SBValue

from .base import _TYPE_CONVERSION
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider


class KonanObjectSyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: SBValue):
        super().__init__(valobj)

        self._children_count = self.evaluate_children_count()
        self._children_names = [self.evaluate_field_name(i) for i in range(self._children_count)]

    def num_children(self):
        return self._children_count

    def has_children(self):
        return self._children_count > 0

    def get_child_index(self, name):
        # if self._children is None:
        return self._children_names.index(name)

    def get_child_at_index(self, index):
        value_type = self.evaluate_field_type(index)
        address = self.evaluate_field_address(index)
        return _TYPE_CONVERSION[int(value_type)](self, self._valobj, address, self._children_names[index])
