"""Tests for `touchlab_kotlin_lldb.types.base.get_type_info`.

Run from the repository root with a stock Python 3 (no LLDB needed):

    python3 -m unittest discover -s LLDBPlugin/tests -v
"""
import unittest

import lldb_stub

lldb_stub.install()

from touchlab_kotlin_lldb.types import base  # noqa: E402

OBJECT_ADDRESS = 0x1029f8028
TYPE_INFO_ADDRESS = 0x101f55e80
TYPE_INFO_TYPE = object()


class FakeProcess:
    """Process memory as a map from address to the pointer-sized word stored there."""

    def __init__(self, words):
        self._words = words

    def ReadPointerFromMemory(self, address, error):
        if address not in self._words:
            error.SetErrorString('memory read failed')
            return 0
        return self._words[address]


class FakeCreatedValue:
    def __init__(self, valid=True):
        self._valid = valid

    def IsValid(self):
        return self._valid


class FakeObjHeaderPointer:
    """An `ObjHeader *` value. It deliberately has no `Cast` or `Dereference`: `get_type_info` must not depend on
    them, because on Xcode 27.x they return an invalid value (touchlab/xcode-kotlin#132)."""

    def __init__(self, process, address=OBJECT_ADDRESS, created=None):
        self._process = process
        self.unsigned = address
        self._created = created or FakeCreatedValue()
        self.created_with = None

    def GetProcess(self):
        return self._process

    def CreateValueFromAddress(self, name, address, value_type):
        self.created_with = (name, address, value_type)
        return self._created


class GetTypeInfoTest(unittest.TestCase):
    def setUp(self):
        original = base.type_info_type
        base.type_info_type = lambda: TYPE_INFO_TYPE
        self.addCleanup(setattr, base, 'type_info_type', original)

    def test_returns_type_info_read_from_memory(self):
        obj = FakeObjHeaderPointer(FakeProcess({
            OBJECT_ADDRESS: TYPE_INFO_ADDRESS,
            TYPE_INFO_ADDRESS: TYPE_INFO_ADDRESS,
        }))

        result = base.get_type_info(obj)

        self.assertIs(result.sb_value, obj._created)
        self.assertEqual(('typeInfoOrMeta_', TYPE_INFO_ADDRESS, TYPE_INFO_TYPE), obj.created_with)

    def test_clears_tag_bits_of_header_word(self):
        obj = FakeObjHeaderPointer(FakeProcess({
            OBJECT_ADDRESS: TYPE_INFO_ADDRESS | 0x3,
            TYPE_INFO_ADDRESS: TYPE_INFO_ADDRESS,
        }))

        self.assertIsNotNone(base.get_type_info(obj))
        self.assertEqual(TYPE_INFO_ADDRESS, obj.created_with[1])

    def test_none_when_header_cannot_be_read(self):
        obj = FakeObjHeaderPointer(FakeProcess({TYPE_INFO_ADDRESS: TYPE_INFO_ADDRESS}))

        self.assertIsNone(base.get_type_info(obj))

    def test_none_when_header_word_is_null_after_masking(self):
        for word in (0x0, 0x3):
            with self.subTest(word=word):
                obj = FakeObjHeaderPointer(FakeProcess({OBJECT_ADDRESS: word}))

                self.assertIsNone(base.get_type_info(obj))

    def test_none_when_type_info_cannot_be_read(self):
        obj = FakeObjHeaderPointer(FakeProcess({OBJECT_ADDRESS: TYPE_INFO_ADDRESS}))

        self.assertIsNone(base.get_type_info(obj))

    def test_none_when_type_info_does_not_point_at_itself(self):
        obj = FakeObjHeaderPointer(FakeProcess({
            OBJECT_ADDRESS: TYPE_INFO_ADDRESS,
            TYPE_INFO_ADDRESS: 0xdead0000,
        }))

        self.assertIsNone(base.get_type_info(obj))

    def test_none_when_created_value_is_invalid(self):
        obj = FakeObjHeaderPointer(
            FakeProcess({OBJECT_ADDRESS: TYPE_INFO_ADDRESS, TYPE_INFO_ADDRESS: TYPE_INFO_ADDRESS}),
            created=FakeCreatedValue(valid=False),
        )

        self.assertIsNone(base.get_type_info(obj))


if __name__ == '__main__':
    unittest.main()
