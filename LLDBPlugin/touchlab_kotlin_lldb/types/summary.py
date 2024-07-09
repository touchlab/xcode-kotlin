import lldb

from .select_provider import select_provider
from .base import get_type_info, obj_header_pointer, single_pointer
from ..util import log, evaluate


def kotlin_object_type_summary(valobj: lldb.SBValue, internal_dict):
    """Hook that is run by lldb to display a Kotlin object."""
    log(lambda: "kotlin_object_type_summary({:#x}: {}: {})".format(valobj.unsigned, valobj.name, valobj.type.name))
    cast_value = obj_header_pointer(valobj)

    type_info = internal_dict["type_info"] if "type_info" in internal_dict.keys() else get_type_info(cast_value)

    if not type_info:
        return cast_value.GetValue()

    provider = select_provider(cast_value, type_info)
    log(lambda: "kotlin_object_type_summary({:#x} - {})".format(cast_value.unsigned, type(provider).__name__))
    provider.update()
    return provider.to_string()


def kotlin_objc_class_summary(objc_obj: lldb.SBValue, internal_dict):
    # """Hook that is run by lldb to display a Kotlin ObjC class wrapper."""
    objc_obj = single_pointer(objc_obj)

    konan_obj = evaluate(
        'void* __result = 0; (ObjHeader*)Kotlin_ObjCExport_refFromObjC((void*){:#x}, &__result)',
        objc_obj.unsigned
    )
    return kotlin_object_type_summary(konan_obj, internal_dict)