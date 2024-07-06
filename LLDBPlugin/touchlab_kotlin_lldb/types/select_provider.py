import lldb

from .base import get_string_symbol_address, get_list_symbol_address, get_map_symbol_address
from .KonanStringSyntheticProvider import KonanStringSyntheticProvider
from .KonanArraySyntheticProvider import KonanArraySyntheticProvider
from .KonanListSyntheticProvider import KonanListSyntheticProvider
from .KonanObjectSyntheticProvider import KonanObjectSyntheticProvider
from .KonanBaseSyntheticProvider import KonanBaseSyntheticProvider
from .KonanMapSyntheticProvider import KonanMapSyntheticProvider
from ..util import log, DebuggerException


def _is_subtype(obj_type_info: lldb.value, type_info: lldb.value) -> bool:
    try:
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
        print(traceback.format_exc())
        return False


def select_provider(valobj: lldb.SBValue, type_info: lldb.value) -> KonanBaseSyntheticProvider:
    log(lambda: "[BEGIN] select_provider")

    try:
        type_info_address = type_info.sbvalue.unsigned
        # valobj.Cast()
        if _is_subtype(type_info, lldb.value(valobj.CreateValueFromAddress("kotlin.String", get_string_symbol_address(), type_info.sbvalue.type))):
            provider = KonanStringSyntheticProvider(valobj, type_info)
        elif _is_subtype(type_info, lldb.value(valobj.CreateValueFromAddress("kotlin.collections.List", get_list_symbol_address(), type_info.sbvalue.type))):
            provider = KonanListSyntheticProvider(valobj, type_info)
        elif _is_subtype(type_info, lldb.value(valobj.CreateValueFromAddress("kotlin.collections.Map", get_map_symbol_address(), type_info.sbvalue.type))):
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
