import lldb

from ..util import log, evaluate
from .base import _TYPE_CONVERSION, array_header_type, runtime_type_alignment, runtime_type_size
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider


class KonanArraySyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        self._children_count = 0

        super().__init__(valobj.Cast(array_header_type()), type_info)

    def update(self) -> bool:
        super().update()
        self._children_count = int(self._val.count_)
        return False

    def num_children(self):
        return self._children_count

    def has_children(self):
        return True

    def get_child_index(self, name):
        log(lambda: "KonanArraySyntheticProvider::get_child_index({})".format(name))
        index = int(name.removeprefix('[').removesuffix(']'))
        return index if (0 <= index < self._children_count) else -1

    def get_child_at_index(self, index):

        value_type = -int(self._type_info.extendedInfo_.fieldsCount_)
        address = self._valobj.unsigned + self._align_up(
            self._valobj.type.GetPointeeType().GetByteSize(),
            int(runtime_type_alignment()[value_type])
        ) + index * int(runtime_type_size()[value_type])
        return _TYPE_CONVERSION[int(value_type)](self, self._valobj, address, '[{}]'.format(index))

    def to_string(self):
        if self._children_count == 1:
            return '1 value'
        else:
            return '{} values'.format(self._children_count)

    @staticmethod
    def _align_up(size, alignment):
        return (size + alignment - 1) & ~(alignment - 1)
