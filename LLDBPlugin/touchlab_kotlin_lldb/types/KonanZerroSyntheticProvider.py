import lldb
from ..util import log, NULL
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider


class KonanZerroSyntheticProvider(object):
    def __init__(self, valobj: lldb.SBValue):
        super().__init__()
        log(lambda: "KonanZerroSyntheticProvider::__init__ {}".format(valobj.name))

    def update(self):
        return True

    def num_children(self):
        log(lambda: "KonanZerroSyntheticProvider::num_children")
        return 0

    def has_children(self):
        log(lambda: "KonanZerroSyntheticProvider::has_children")
        return False

    def get_child_index(self, name):
        log(lambda: "KonanZerroSyntheticProvider::get_child_index")
        return 0

    def get_child_at_index(self, index):
        log(lambda: "KonanZerroSyntheticProvider::get_child_at_index")
        return None

    def to_string(self):
        log(lambda: "KonanZerroSyntheticProvider::to_string")
        return NULL

    def __getattr__(self, item):
        pass
