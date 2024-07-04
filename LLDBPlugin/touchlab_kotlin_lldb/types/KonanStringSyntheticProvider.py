import lldb

from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from ..util import kotlin_object_to_string, log


class KonanStringSyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: lldb.SBValue):
        super().__init__(valobj)

        s = kotlin_object_to_string(self._process, self._valobj.unsigned)
        self._representation = '"{}"'.format(s) if s else self._valobj.GetValue()

    def num_children(self):
        return 0

    def has_children(self):
        return False

    def get_child_index(self, _):
        return None

    def get_child_at_index(self, _):
        return None

    def to_string(self):
        return self._representation
