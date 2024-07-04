from lldb import SBValue

from .KonanArraySyntheticProvider import KonanArraySyntheticProvider
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from ..util import DebuggerException
from ..util.expression import EXPRESSION_OPTIONS


class KonanMapSyntheticProvider(KonanBaseSyntheticProvider):
    def __init__(self, valobj: SBValue):
        super().__init__(valobj)

        real_children_count = self.evaluate_children_count()
        for i in range(real_children_count):
            name = self.evaluate_field_name(i)
            if name == 'keysArray':
                address = self.evaluate_field_address(i)
                backing_value = self._valobj.CreateValueFromAddress(
                    name,
                    address,
                    self._valobj.type,
                )
                self._keys = KonanArraySyntheticProvider(backing_value)
            elif name == 'valuesArray':
                address = self.evaluate_field_address(i)
                backing_value = self._valobj.CreateValueFromAddress(
                    name,
                    address,
                    self._valobj.type,
                )
                self._values = KonanArraySyntheticProvider(backing_value)

        if self._keys is None or self._values is None:
            raise DebuggerException(
                "Couldn't find backing for map {:#x}, name: {}".format(self._valobj.unsigned, self._valobj.name)
            )

    def num_children(self):
        return self._keys.num_children()

    def has_children(self):
        return self._keys.has_children()

    def get_child_index(self, name):
        # TODO: Not correct, we need to look at the values which this doesn't do
        return self._keys.get_child_index(name)

    def get_child_at_index(self, index):
        return self._valobj.CreateValueFromExpression(
            f'[{index}]',
            '(MapEntry){{ (ObjHeader*){:#x}, (ObjHeader*){:#x} }};'.format(
                self._keys.get_child_at_index(index).unsigned,
                self._values.get_child_at_index(index).unsigned,
            ),
            EXPRESSION_OPTIONS,
        )

    def to_string(self):
        children_count = self._keys.num_children()
        if children_count == 1:
            return '1 key/value pair'
        else:
            return '{} key/value pairs'.format(children_count)
