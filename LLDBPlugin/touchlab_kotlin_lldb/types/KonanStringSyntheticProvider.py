import lldb

from .base import array_header_type
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from ..util import kotlin_object_to_string, log


class KonanStringSyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        super().__init__(valobj.Cast(array_header_type()), type_info)

    def update(self):
        return True

    def num_children(self):
        return 0

    def has_children(self):
        return False

    def get_child_index(self, _):
        return None

    def get_child_at_index(self, _):
        return None

    def to_string(self):
        s = kotlin_object_to_string(self._process, self._valobj.unsigned)
        if s is None:
            return self._valobj.GetValue()
        else:
            return '"{}"'.format(s)
