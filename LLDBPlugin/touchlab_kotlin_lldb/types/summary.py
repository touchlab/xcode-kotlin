import lldb

from .select_provider import select_provider
from .base import get_type_info
from ..util import log, NULL, evaluate


def kotlin_object_type_summary(valobj: lldb.SBValue, internal_dict):
    """Hook that is run by lldb to display a Kotlin object."""
    log(lambda: "kotlin_object_type_summary({:#x}: {}: {})".format(valobj.unsigned, valobj.name, valobj.type.name))
    if valobj.unsigned == 0:
        return NULL
    type_info = internal_dict["type_info"] if "type_info" in internal_dict.keys() else get_type_info(valobj)

    if not type_info:
        return valobj.GetValue()

    provider = select_provider(valobj, type_info)
    log(lambda: "kotlin_object_type_summary({:#x} - {})".format(valobj.unsigned, type(provider).__name__))
    provider.update()
    return provider.to_string()


def kotlin_objc_class_summary(valobj: lldb.SBValue, internal_dict):
    # """Hook that is run by lldb to display a Kotlin ObjC class wrapper."""
    if valobj.unsigned == 0:
        return NULL

    obj = evaluate(
        'void* __result = 0; (ObjHeader*)Kotlin_ObjCExport_refFromObjC((void*){:#x}, &__result)',
        valobj.unsigned
    )
    return kotlin_object_type_summary(obj, internal_dict)
