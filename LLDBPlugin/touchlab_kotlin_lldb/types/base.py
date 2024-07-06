from typing import Optional

import lldb

from ..util import strip_quotes, log, evaluate
from ..cache import LLDBCache

KOTLIN_OBJ_HEADER_TYPE = lldb.SBTypeNameSpecifier('ObjHeader *', lldb.eMatchTypeNormal)
KOTLIN_ARRAY_HEADER_TYPE = lldb.SBTypeNameSpecifier('ArrayHeader *', lldb.eMatchTypeNormal)
KOTLIN_CATEGORY = 'Kotlin'

# _TYPE_CONVERSION = [
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "(__konan_safe_void_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.synthetic_child_from_address(name, address, value.type),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(int8_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(int16_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(int32_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(int64_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(__konan_safe_float_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(__konan_safe_double_t *){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(__konan_safe_void_t **){:#x}".format(address)),
#     lambda obj, value, address, name: value.CreateValueFromExpression(name, "*(__konan_safe_bool_t *){:#x}".format(address)),
#     lambda obj, value, address, name: None
# ]

_TYPE_CONVERSION = [
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeVoid).GetPointerType()),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address, value.type),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeChar)),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeShort)),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeInt)),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeLongLong)),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeFloat)),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeDouble)),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeVoid).GetPointerType()),
    lambda obj, value, address, name: value.synthetic_child_from_address(name, address,
                                                                         lldb.debugger.GetSelectedTarget().GetBasicType(
                                                                             lldb.eBasicTypeBool)),
    lambda obj, value, address, name: None,
]

_TYPES = [
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeVoid).GetPointerType(),
    lambda x: x.GetType(),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeChar),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeShort),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeInt),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeLongLong),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeFloat),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeDouble),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeVoid).GetPointerType(),
    lambda x: x.GetType().GetBasicType(lldb.eBasicTypeBool)
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
        self._runtime_type_size = lldb.value(lldb.debugger.GetSelectedTarget().EvaluateExpression('runtimeTypeSize'))
    return self._runtime_type_size


def runtime_type_alignment() -> lldb.value:
    self = LLDBCache.instance()
    if self._runtime_type_alignment is None:
        self._runtime_type_alignment = lldb.value(
            lldb.debugger.GetSelectedTarget().EvaluateExpression('runtimeTypeAlignment')
        )
    return self._runtime_type_alignment


def _symbol_loaded_address(name, debugger) -> int:
    target: lldb.SBTarget = debugger.GetSelectedTarget()
    candidates = target.process.selected_thread.GetSelectedFrame().module.symbol[name]
    # take first
    for candidate in candidates:
        address = candidate.GetStartAddress().GetLoadAddress(target)
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
