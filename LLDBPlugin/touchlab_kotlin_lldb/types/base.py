from typing import Optional

import lldb

from ..util import strip_quotes, log, evaluate
from ..cache import LLDBCache

KOTLIN_OBJ_HEADER_TYPE = lldb.SBTypeNameSpecifier('ObjHeader', lldb.eMatchTypeNormal)
KOTLIN_ARRAY_HEADER_TYPE = lldb.SBTypeNameSpecifier('ArrayHeader', lldb.eMatchTypeNormal)
KOTLIN_CATEGORY = 'Kotlin'

_TYPE_CONVERSION = [
    # INVALID
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeVoid).GetPointerType()
    ),
    # OBJECT
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, obj_header_type()
    ),
    # INT8
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeChar)
    ),
    # INT16
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeShort)
    ),
    # INT32
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeInt)
    ),
    # INT64
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeLongLong)
    ),
    # FLOAT32
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeFloat)
    ),
    # FLOAT64
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeDouble)
    ),
    # NATIVE_PTR
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeVoid).GetPointerType()
    ),
    # BOOLEAN
    lambda obj, value, address, name: value.synthetic_child_from_address(
        name, address, lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeBool)
    ),
    # TODO: VECTOR128
    lambda obj, value, address, name: None,
]


def single_pointer(valobj: lldb.SBValue) -> lldb.SBValue:
    non_synthetic_value = valobj.GetNonSyntheticValue()

    # TODO: Test how this behaves when stopped in C++
    # In case we've stopped in Swift, this will be true.
    if non_synthetic_value.type.IsReferenceType():
        return non_synthetic_value

    while non_synthetic_value.type.GetPointeeType().IsPointerType():
        non_synthetic_value = non_synthetic_value.Dereference()

    if not non_synthetic_value.type.IsPointerType():
        non_synthetic_value = non_synthetic_value.AddressOf()

    return non_synthetic_value


def obj_header_pointer(valobj: lldb.SBValue) -> lldb.SBValue:
    return single_pointer(valobj).Cast(obj_header_type())


def get_runtime_type(variable):
    return strip_quotes(evaluate("(char *)Konan_DebugGetTypeName({:#x})", variable.unsigned).summary)


def type_info_type() -> lldb.SBType:
    self = LLDBCache.instance()
    if self._type_info_type is None:
        self._type_info_type = evaluate('(TypeInfo*)0x0').GetNonSyntheticValue().type
    return self._type_info_type


def obj_header_type() -> lldb.SBType:
    self = LLDBCache.instance()
    if self._obj_header_type is None:
        self._obj_header_type = evaluate('(ObjHeader*)0x0').GetNonSyntheticValue().type
    return self._obj_header_type


def array_header_type() -> lldb.SBType:
    self = LLDBCache.instance()
    if self._array_header_type is None:
        self._array_header_type = evaluate('(ArrayHeader*)0x0').GetNonSyntheticValue().type
    return self._array_header_type


def runtime_type_size() -> lldb.value:
    self = LLDBCache.instance()
    if self._runtime_type_size is None:
        self._runtime_type_size = lldb.value(evaluate('runtimeTypeSize'))
    return self._runtime_type_size


def runtime_type_alignment() -> lldb.value:
    self = LLDBCache.instance()
    if self._runtime_type_alignment is None:
        self._runtime_type_alignment = lldb.value(
            evaluate('runtimeTypeAlignment')
        )
    return self._runtime_type_alignment


def _symbol_loaded_address(name: str, target: lldb.SBTarget) -> int:
    candidates = target.FindSymbols(name)
    # take first
    for candidate in candidates:
        address = candidate.symbol.GetStartAddress().GetLoadAddress(target)
        log(lambda: "_symbol_loaded_address:{} {:#x}".format(name, address))
        return address

    return 0


def _get_konan_class_symbol_value(cls_name: str) -> lldb.value:
    target = lldb.debugger.GetSelectedTarget()
    address = _symbol_loaded_address(f'kclass:{cls_name}', target)
    return lldb.value(
        target.CreateValueFromAddress(
            cls_name,
            lldb.SBAddress(address, target),
            type_info_type(),
        )
    )


def get_string_symbol() -> lldb.value:
    self = LLDBCache.instance()
    if self._string_symbol_value is None:
        self._string_symbol_value = _get_konan_class_symbol_value('kotlin.String')
    return self._string_symbol_value


def get_list_symbol() -> lldb.value:
    self = LLDBCache.instance()
    if self._list_symbol_value is None:
        self._list_symbol_value = _get_konan_class_symbol_value('kotlin.collections.List')
    return self._list_symbol_value


def get_map_symbol() -> lldb.value:
    self = LLDBCache.instance()
    if self._map_symbol_value is None:
        self._map_symbol_value = _get_konan_class_symbol_value('kotlin.collections.Map')
    return self._map_symbol_value


class KnownValueType:
    ANY = 0
    STRING = 1
    ARRAY = 2
    LIST = 3
    MAP = 4

    entries = [ANY, STRING, ARRAY, LIST, MAP]

    @staticmethod
    def value_of(raw: int):
        assert KnownValueType.ANY <= raw <= KnownValueType.MAP
        return KnownValueType.entries[raw]


def void_type() -> lldb.SBType:
    return lldb.debugger.GetSelectedTarget().GetBasicType(lldb.eBasicTypeVoid)


def get_type_info(obj: lldb.SBValue) -> Optional[lldb.value]:
    possible_type_info = obj.CreateValueFromAddress(
        "typeInfoOrMeta_",
        obj.Cast(void_type().GetPointerType().GetPointerType()).Dereference().unsigned & ~0x3,
        type_info_type(),
    )
    verification = possible_type_info.Cast(possible_type_info.type.GetPointerType()).Dereference()

    if possible_type_info.unsigned == verification.unsigned and possible_type_info.IsValid() and possible_type_info.unsigned != 0:
        return lldb.value(possible_type_info)
    else:
        return None
