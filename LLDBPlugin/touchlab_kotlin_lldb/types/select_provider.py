import lldb

from .base import get_string_symbol, get_list_symbol, get_map_symbol
from .KonanStringSyntheticProvider import KonanStringSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider
from .KonanListSyntheticProvider import KonanListSyntheticProvider
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from .KonanMapSyntheticProvider import KonanMapSyntheticProvider
from ..util import log


def _is_subtype(obj_type_info: lldb.value, type_info: lldb.value) -> bool:
    try:
        # noinspection PyPep8Naming
        TF_INTERFACE = 1 << 2
        # If it is an interface - check in list of implemented interfaces.
        if (int(type_info.flags_) & TF_INTERFACE) != 0:
            for i in range(int(obj_type_info.implementedInterfacesCount_)):
                if obj_type_info.implementedInterfaces_[i] == type_info:
                    return True
            return False
        while obj_type_info != 0 and obj_type_info != type_info:
            obj_type_info = obj_type_info.superType_

        return obj_type_info != 0
    except BaseException as e:
        import traceback
        traceback.print_exc()
        return False


def select_provider(valobj: lldb.SBValue, type_info: lldb.value) -> KonanBaseSyntheticProvider:
    log(lambda: "[BEGIN] select_provider")

    try:
        if _is_subtype(type_info, get_string_symbol()):
            provider = KonanStringSyntheticProvider(valobj, type_info)
        elif _is_subtype(type_info, get_list_symbol()):
            provider = KonanListSyntheticProvider(valobj, type_info)
        elif _is_subtype(type_info, get_map_symbol()):
            provider = KonanMapSyntheticProvider(valobj, type_info)
        elif int(type_info.instanceSize_) < 0:
            provider = KonanArraySyntheticProvider(valobj, type_info)
        else:
            provider = KonanObjectSyntheticProvider(valobj, type_info)

    except:
        import traceback
        import sys
        sys.stderr.write(
            "Couldn't select provider for value {:#x} (name={}).\n".format(
                valobj.unsigned,
                valobj.name,
            )
        )
        traceback.print_exc()
        sys.stderr.write('\nFalling back to KonanObjectSyntheticProvider.\n')
        provider = KonanObjectSyntheticProvider(valobj, type_info)

    log(lambda: "[END] select_provider = {}".format(
        provider,
    ))
    return provider
