from typing import Optional

import lldb

from .KonanArraySyntheticProvider import KonanArraySyntheticProvider
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .base import get_type_info
from ..util import DebuggerException
from ..util.expression import EXPRESSION_OPTIONS


class KonanMapSyntheticProvider(KonanObjectSyntheticProvider):
    def __init__(self, valobj: lldb.SBValue, type_info: lldb.value):
        self._keys: KonanArraySyntheticProvider = None  # type: ignore
        self._values: KonanArraySyntheticProvider = None  # type: ignore

        super().__init__(valobj, type_info)

    def update(self):
        super().update()

        if self._keys is None or self._values is None:
            keys: Optional[KonanArraySyntheticProvider] = None
            values: Optional[KonanArraySyntheticProvider] = None

            for index, name in enumerate(self._children_names):
                if name == 'keysArray':
                    keys = self._create_backing(index, name)
                elif name == 'valuesArray':
                    values = self._create_backing(index, name)

            if keys is None or values is None:
                raise DebuggerException(
                    "Couldn't find backing for map {:#x}, name: {}".format(self._valobj.unsigned, self._valobj.name)
                )
            else:
                self._keys = keys
                self._values = values

        self._keys.update()
        self._values.update()

        return False

    def num_children(self):
        return self._keys.num_children()

    def has_children(self):
        return True

    def get_child_index(self, name):
        # TODO: Not correct, we need to look at the values which this doesn't do
        return self._keys.get_child_index(name)

    def get_child_at_index(self, index):
        lldb.debugger.GetSelectedTarget().GetProcess()
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
