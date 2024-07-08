from typing import Optional

import lldb

from ..util import strip_quotes, log, evaluate
from ..cache import LLDBCache

KOTLIN_OBJ_HEADER_TYPE = lldb.SBTypeNameSpecifier('ObjHeader *', lldb.eMatchTypeNormal)
KOTLIN_ARRAY_HEADER_TYPE = lldb.SBTypeNameSpecifier('ArrayHeader *', lldb.eMatchTypeNormal)
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


def get_runtime_type(variable):
    return strip_quotes(evaluate("(char *)Konan_DebugGetTypeName({:#x})", variable.unsigned).summary)


def type_info_type() -> lldb.SBType:
    self = LLDBCache.instance()
    if self._type_info_type is None:
        self._type_info_type = evaluate('(TypeInfo*)0x0').type
    return self._type_info_type


def obj_header_type() -> lldb.SBType:
    self = LLDBCache.instance()
    if self._obj_header_type is None:
        self._obj_header_type = evaluate('(ObjHeader*)0x0').type
    return self._obj_header_type


def array_header_type() -> lldb.SBType:
    self = LLDBCache.instance()
    if self._array_header_type is None:
        self._array_header_type = evaluate('(ArrayHeader*)0x0').type
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


def _symbol_loaded_address(name: str, debugger: lldb.SBDebugger) -> int:
    target: lldb.SBTarget = debugger.GetSelectedTarget()
    candidates = target.FindSymbols(name)
    # take first
    for candidate in candidates:
        address = candidate.symbol.GetStartAddress().GetLoadAddress(target)
        log(lambda: "_symbol_loaded_address:{} {:#x}".format(name, address))
        return address

    return 0


def get_string_symbol_address() -> int:
    self = LLDBCache.instance()
    if self._string_symbol_addr is None:
        self._string_symbol_addr = _symbol_loaded_address('kclass:kotlin.String', lldb.debugger)
    return self._string_symbol_addr


def get_list_symbol_address() -> int:
    self = LLDBCache.instance()
    if self._list_symbol_addr is None:
        self._list_symbol_addr = _symbol_loaded_address('kclass:kotlin.collections.List', lldb.debugger)
    return self._list_symbol_addr


def get_map_symbol_address() -> int:
    self = LLDBCache.instance()
    if self._map_symbol_addr is None:
        self._map_symbol_addr = _symbol_loaded_address('kclass:kotlin.collections.Map', lldb.debugger)
    return self._map_symbol_addr


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
