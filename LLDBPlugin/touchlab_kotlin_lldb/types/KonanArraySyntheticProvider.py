from lldb import SBSyntheticValueProvider, SBValue

from ..util import log, evaluate
from .base import _TYPE_CONVERSION
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider


class KonanArraySyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: SBValue):
        super().__init__(valobj)

        self._children_count = self.evaluate_children_count()

    def num_children(self):
        return self._children_count

    def has_children(self):
        return self._children_count > 0

    def get_child_index(self, name):
        log(lambda: "KonanArraySyntheticProvider::get_child_index({})".format(name))
        index = int(name.removeprefix('[').removesuffix(']'))
        return index if (0 <= index < self._children_count) else -1

    def get_child_at_index(self, index):
        value_type = self.evaluate_field_type(index)
        address = self.evaluate_field_address(index)
        return _TYPE_CONVERSION[int(value_type)](self, self._valobj, address, '[{}]'.format(index))

    def to_string(self):
        if self._children_count == 1:
            return '1 value'
        else:
            return '{} values'.format(self._children_count)
