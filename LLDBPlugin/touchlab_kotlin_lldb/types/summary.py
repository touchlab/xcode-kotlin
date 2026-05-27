from typing import Optional

import lldb

from .select_provider import select_provider
from .base import get_type_info, obj_header_pointer, objc_bridged_obj_header, single_pointer
from ..util import log, evaluate, strip_quotes


def _objc_class_name(objc_ptr: int) -> Optional[str]:
    """Return the ObjC class name for an instance pointer, or None if it can't
    be read. Used to label a bridged Kotlin object with the class the user
    actually wrote (e.g. their Swift type) instead of a bare address."""
    name = evaluate('(const char*)object_getClassName((void*){:#x})', objc_ptr)
    if name is None or not name.IsValid() or name.error.Fail():
        return None
    return strip_quotes(name.summary) or None


def _objc_bridge_summary_fallback(cast_value: lldb.SBValue) -> str:
    """Build a summary for a Kotlin object that the Kotlin runtime can't
    describe via Konan_DebugObjectToUtf8Array (typically a Kotlin wrapper
    around a Swift class implementing a Kotlin interface). It looks up the
    underlying ObjC pointer via Kotlin_ObjCExport_refToObjC and the instance's
    ObjC class name so the user sees something like `SwiftCallback objc@0x…`
    instead of `None`."""
    if cast_value.unsigned == 0:
        return "@0x0"
    objc_ptr = evaluate(
        '(void*)Kotlin_ObjCExport_refToObjC((ObjHeader*){:#x})',
        cast_value.unsigned,
    )
    if objc_ptr is not None and objc_ptr.error.Success() and objc_ptr.unsigned != 0:
        class_name = _objc_class_name(objc_ptr.unsigned)
        if class_name:
            return "{} objc@{:#x}".format(class_name, objc_ptr.unsigned)
        return "objc@{:#x}".format(objc_ptr.unsigned)
    return "@{:#x}".format(cast_value.unsigned)


def kotlin_object_type_summary(valobj: lldb.SBValue, internal_dict):
    """Hook that is run by lldb to display a Kotlin object."""
    log(lambda: "kotlin_object_type_summary({:#x}: {}: {})".format(valobj.unsigned, valobj.name, valobj.type.name))
    cast_value = obj_header_pointer(valobj)

    type_info = internal_dict["type_info"] if "type_info" in internal_dict.keys() else get_type_info(cast_value)

    if not type_info:
        bridged = objc_bridged_obj_header(cast_value)
        if bridged is not None:
            bridged_type_info = get_type_info(bridged)
            if bridged_type_info:
                log(lambda: "kotlin_object_type_summary: bridged ObjC->Kotlin {:#x}->{:#x}".format(
                    cast_value.unsigned, bridged.unsigned))
                provider = select_provider(bridged, bridged_type_info)
                provider.update()
                bridged_summary = provider.to_string()
                if bridged_summary is not None:
                    return bridged_summary
            return _objc_bridge_summary_fallback(bridged)
        return cast_value.GetValue()

    provider = select_provider(cast_value, type_info)
    log(lambda: "kotlin_object_type_summary({:#x} - {})".format(cast_value.unsigned, type(provider).__name__))
    provider.update()
    summary = provider.to_string()
    if summary is None and cast_value.unsigned != 0:
        return _objc_bridge_summary_fallback(cast_value)
    return summary


def kotlin_objc_class_summary(objc_obj: lldb.SBValue, internal_dict):
    """Hook that is run by lldb to display a Kotlin ObjC class wrapper."""
    objc_obj = single_pointer(objc_obj)

    konan_obj = evaluate(
        'void* __result = 0; (ObjHeader*)Kotlin_ObjCExport_refFromObjC((void*){:#x}, &__result)',
        objc_obj.unsigned
    )
    return kotlin_object_type_summary(konan_obj, internal_dict)
