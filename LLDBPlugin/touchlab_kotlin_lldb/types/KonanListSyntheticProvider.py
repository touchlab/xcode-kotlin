from lldb import SBValue, SBType

from ..util import log, DebuggerException
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider


class KonanListSyntheticProvider(KonanBaseSyntheticProvider):
    __possible_backing_properties = {'backing', '$this_asList', 'backingArray'}

    def __init__(self, valobj: SBValue):
        super().__init__(valobj)

        real_children_count = self.evaluate_children_count()

        for i in range(real_children_count):
            name = self.evaluate_field_name(i)
            if name in KonanListSyntheticProvider.__possible_backing_properties:
                address = self.evaluate_field_address(i)
                backing_value = self._valobj.CreateValueFromAddress(
                    name,
                    address,
                    self._valobj.type,
                )
                self._backing = KonanArraySyntheticProvider(backing_value)
                return

        raise DebuggerException(
            "Couldn't find backing for list {:#x}, name: {}".format(self._valobj.unsigned, self._valobj.name)
        )

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
