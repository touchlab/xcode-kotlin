import lldb
from lldb import SBValue, SBTypeNameSpecifier

from ..util import strip_quotes, log, evaluate
from ..cache import LLDBCache

KOTLIN_NATIVE_TYPE = 'ObjHeader *'
KOTLIN_NATIVE_TYPE_SPECIFIER = SBTypeNameSpecifier(KOTLIN_NATIVE_TYPE, lldb.eMatchTypeNormal)
KOTLIN_CATEGORY = 'Kotlin'

_TYPE_CONVERSION = [
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(__konan_safe_void_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromAddress(name, address, value.type),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(int8_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(int16_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(int32_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(int64_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(__konan_safe_float_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(__konan_safe_double_t *){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(__konan_safe_void_t **){:#x}".format(address)),
    lambda obj, value, address, name: value.CreateValueFromExpression(name, "(__konan_safe_bool_t *){:#x}".format(address)),
    lambda obj, value, address, name: None
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

def _symbol_loaded_address(name, debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    candidates = frame.module.symbol[name]
    # take first
    for candidate in candidates:
        address = candidate.GetStartAddress().GetLoadAddress(target)
        log(lambda: "_symbol_loaded_address:{} {:#x}".format(name, address))
        return address

    return 0


def GetStringSymbolAddress() -> int:
    self = LLDBCache.instance()
    if self._string_symbol_addr is None:
        self._string_symbol_addr = _symbol_loaded_address('kclass:kotlin.String', lldb.debugger)
    return self._string_symbol_addr


def GetListSymbolAddress() -> int:
    self = LLDBCache.instance()
    if self._list_symbol_addr is None:
        self._list_symbol_addr = _symbol_loaded_address('kclass:kotlin.collections.List', lldb.debugger)
    return self._list_symbol_addr


def GetMapSymbolAddress() -> int:
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


def get_known_type(value: SBValue):
    is_string = '(__konan_safe_int_t)Konan_DebugIsInstance({:#x}, {:#x}) ? {}'.format(
        value.unsigned,
        GetStringSymbolAddress(),
        KnownValueType.STRING,
    )
    is_array = '(__konan_safe_int_t)Konan_DebugIsArray({:#x}) ? {}'.format(
        value.unsigned,
        KnownValueType.ARRAY,
    )
    is_list = '(__konan_safe_int_t)Konan_DebugIsInstance({:#x}, {:#x}) ? {}'.format(
        value.unsigned,
        GetListSymbolAddress(),
        KnownValueType.LIST,
    )
    is_map = '(__konan_safe_int_t)Konan_DebugIsInstance({:#x}, {:#x}) ? {}'.format(
        value.unsigned,
        GetMapSymbolAddress(),
        KnownValueType.MAP,
    )

    raw = evaluate(
        '{} : {} : {} : {} : {}',
        is_string,
        is_array,
        is_list,
        is_map,
        KnownValueType.ANY,
    ).unsigned
    log(lambda: "get_known_type:{}".format(raw))
    known_type = KnownValueType.value_of(raw)
    log(lambda: "get_known_type:{}".format(known_type))
    return known_type

# did_it = False

def type_info(value):
    """
    This method checks self-referencing of pointer of first member of TypeInfo including case when object has an
    meta-object pointed by TypeInfo. Two lower bits are reserved for memory management needs see runtime/src/main/cpp/Memory.h.
    """
    log(lambda: "type_info({:#x}: {})".format(value.unsigned, value.GetTypeName()))
    if value.GetTypeName() != KOTLIN_NATIVE_TYPE:
        return None
    # global did_it
    # if not did_it:
    #     top_level_evaluate(
    #         'typedef void __konan_safe_void_t;'
    #         'typedef int __konan_safe_int_t;'
    #     )
    #     did_it = True
    result = evaluate(
        "*(__konan_safe_void_t**)((uintptr_t)(*(__konan_safe_void_t**){0:#x}) & ~0x3) == **(__konan_safe_void_t***)((uintptr_t)(*(__konan_safe_void_t**){0:#x}) & ~0x3) "
        "? *(__konan_safe_void_t **)((uintptr_t)(*(__konan_safe_void_t**){0:#x}) & ~0x3) : (__konan_safe_void_t *)0",
        value.unsigned
    )

    return result.unsigned if result.IsValid() and result.unsigned != 0 else None
