from lldb import SBValue

from .KonanArraySyntheticProvider import KonanArraySyntheticProvider
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .KonanProxyTypeProvider import KonanProxyTypeProvider, select_provider
from .KonanStringSyntheticProvider import KonanStringSyntheticProvider
from .KonanListSyntheticProvider import KonanListSyntheticProvider
from .base import KOTLIN_NATIVE_TYPE, KOTLIN_NATIVE_TYPE_SPECIFIER, KOTLIN_CATEGORY, type_info
from ..util import log, NULL


def kotlin_object_type_summary(valobj: SBValue, internal_dict):
    """Hook that is run by lldb to display a Kotlin object."""
    log(lambda: "kotlin_object_type_summary({:#x}: {})".format(valobj.unsigned, valobj.type.name))
    if valobj.GetTypeName() != KOTLIN_NATIVE_TYPE:
        if valobj.GetValue() is None:
            return NULL
        return valobj.GetValue()

    if valobj.unsigned == 0:
        return NULL
    tip = internal_dict["type_info"] if "type_info" in internal_dict.keys() else type_info(valobj)

    if not tip:
        return valobj.GetValue()

    provider = select_provider(valobj)
    log(lambda: "kotlin_object_type_summary({:#x} - {})".format(valobj.unsigned, type(provider).__name__))
    return provider.to_string()
