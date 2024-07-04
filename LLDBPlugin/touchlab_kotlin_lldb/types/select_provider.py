from lldb import SBValue

from .base import get_known_type, KnownValueType
from .KonanStringSyntheticProvider import KonanStringSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider
from .KonanListSyntheticProvider import KonanListSyntheticProvider
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from .KonanMapSyntheticProvider import KonanMapSyntheticProvider
from ..util import log, DebuggerException


def select_provider(valobj: SBValue) -> KonanBaseSyntheticProvider:
    log(lambda: "[BEGIN] select_provider")
    known_type = get_known_type(valobj)

    try:
        if known_type == KnownValueType.STRING:
            ret = KonanStringSyntheticProvider(valobj)
        elif known_type == KnownValueType.ARRAY:
            ret = KonanArraySyntheticProvider(valobj)
        elif known_type == KnownValueType.ANY:
            ret = KonanObjectSyntheticProvider(valobj)
        elif known_type == KnownValueType.LIST:
            ret = KonanListSyntheticProvider(valobj)
        elif known_type == KnownValueType.MAP:
            ret = KonanMapSyntheticProvider(valobj)
        else:
            # TODO: Log warning that we didn't handle a known_type
            ret = KonanObjectSyntheticProvider(valobj)
    except DebuggerException as e:
        import sys
        sys.stderr.write(
            "Couldn't select provider for value {:#x} (name={}) with known type of {}.\n".format(
                valobj.unsigned,
                valobj.name,
                known_type
            )
        )
        sys.stderr.write(e.msg)
        sys.stderr.write('\nFalling back to KonanObjectSyntheticProvider.\n')
        ret = KonanObjectSyntheticProvider(valobj)

    log(lambda: "[END] select_provider = {} (known_type: {})".format(
        ret,
        known_type,
    ))
    return ret
