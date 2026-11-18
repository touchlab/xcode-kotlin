"""Minimal stand-in for the `lldb` module so plugin logic can be unit tested outside of a debugger session.

`install()` must run before the first import of `touchlab_kotlin_lldb`. Only the pieces the tests rely on are
modelled; everything else is a `MagicMock` attribute. These tests exercise the plugin's own logic, not LLDB.
"""
import os
import sys
from unittest import mock

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeSBError:
    def __init__(self):
        self._failed = False

    def SetErrorString(self, _message):
        self._failed = True

    def Success(self):
        return not self._failed

    def Fail(self):
        return self._failed

    success = property(Success)
    fail = property(Fail)


class FakeValue:
    """Stands in for `lldb.value`, which wraps an `SBValue`."""

    def __init__(self, sb_value):
        self.sb_value = sb_value


def install():
    existing = sys.modules.get('lldb')
    if existing is not None and getattr(existing, 'IS_TEST_STUB', False):
        return
    stub = mock.MagicMock(name='lldb')
    stub.IS_TEST_STUB = True
    stub.SBError = FakeSBError
    stub.value = FakeValue
    sys.modules['lldb'] = stub
    if PLUGIN_DIR not in sys.path:
        sys.path.insert(0, PLUGIN_DIR)
