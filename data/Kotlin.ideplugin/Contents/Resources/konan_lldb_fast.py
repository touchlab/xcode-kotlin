#!/usr/bin/python

##
# Copyright 2019 Touchlab
#
# Copyright 2010-2017 JetBrains s.r.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Modified from original to better support interactive tools (specifically Xcode)
# Some additional mods to better match how examples work http://llvm.org/svn/llvm-project/lldb/trunk/examples/synthetic/bitfield/example.py

#
# (lldb) command script import llvmDebugInfoC/src/scripts/konan_lldb.py
# (lldb) p kotlin_variable
#

import lldb
import struct

NULL = 'null'

def lldb_val_to_ptr(lldb_val):
    addr = lldb_val.GetValueAsUnsigned()
    return '((struct ObjHeader *) {:#x})'.format(addr)

def evaluate(expr):
    result = lldb.debugger.GetSelectedTarget().EvaluateExpression(expr, lldb.SBExpressionOptions())
    # print "evaluate '" + expr +"' - "+ str(result)
    return result

_debug_string_buffer = 0

def debug_string_buffer_ptr():
    global _debug_string_buffer
    if _debug_string_buffer == 0:
        _debug_string_buffer = long(evaluate("(char *)Konan_DebugBuffer()").unsigned)

    return _debug_string_buffer

# This method performs multiple checks in a single statement to reduce the number of calls through lldb to the underlying
# process. First we check that the typeinfo pointer indicates we're not a meta class. Then we check if this is a string, and
# if so, copy the string to the debug buffer and return the length. That is encoded by adding 10 and negating. So, if the
# result is -13, that's a string of length 3. -26, 16. Etc. If not, check if array. If so , return -2. If not that, we assume
# a standard K/N object, and return the typeinfo pointer. TypeInfo definitions are cached by pointer, which greatly reduces
# lldb process call volume.

def super_big_type_check(lldb_val):
    if str(lldb_val.type) != "struct ObjHeader *" or lldb_val.unsigned == 0 or lldb_val.GetName().startswith("&"):
        # print str(lldb_val.type)
        return NO_TYPE_KNOWN

    ptr_str = lldb_val_to_ptr(lldb_val)
    expr_check = "(*(void **)((uintptr_t)(*(void**){0}) & ~0x3) != **(void***)((uintptr_t)(*(void**){0}) & ~0x3) ? -3 : (".format(lldb_val.unsigned)
    expr_string_copy = "(int)Konan_DebugObjectToUtf8Array({}, (char *)Konan_DebugBuffer(), (int)Konan_DebugBufferSize())".format(ptr_str)
    expr = "(long)((bool)IsInstance({}, {}) ? -({} + {}) : ((int)Konan_DebugIsArray({}) == 1 ? -2 : (uintptr_t)(*(void **)((uintptr_t)(*(void**){}) & ~0x3))))" \
        .format(ptr_str, "theStringTypeInfo", expr_string_copy, STRING_SIZE_OFFSET, ptr_str, lldb_val.unsigned)

    full_statement = expr_check + expr + "))"

    result = evaluate(full_statement)
    if result.IsValid():
        callResult = result.GetValue()
        if callResult is None:
            return NO_TYPE_KNOWN

        return long(callResult)
    else:
        return NO_TYPE_KNOWN

def kotlin_object_type_summary(lldb_val, internal_dict):
    """Hook that is run by lldb to display a Kotlin object."""
    fallback = lldb_val.GetValue()
    if str(lldb_val.type) != "struct ObjHeader *":
        return fallback

    type_check_result = super_big_type_check(lldb_val)

    if type_check_result == NO_TYPE_KNOWN:
        return NULL

    ptr = lldb_val_to_ptr(lldb_val)
    if ptr is None:
        return fallback

    return select_provider(lldb_val, type_check_result).to_string()

def _child_type_global(ptr, index):
    return evaluate("(int)Konan_DebugGetFieldType({}, {})".format(ptr, index)).GetValueAsUnsigned()

TYPE_CONVERSIONS = [
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(void *){:#x}".format(address)),
    lambda address, name, provider: provider._create_synthetic_child(name),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(int8_t *){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(int16_t *){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(int32_t *){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(int64_t *){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(float *){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(double *){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(void **){:#x}".format(address)),
    lambda address, name, provider: provider._valobj.CreateValueFromExpression(name, "(bool *){:#x}".format(address)),
    lambda address, name, provider: None
]

def _type_conversion(index, address, name, provider):
    if len(TYPE_CONVERSIONS) > index:
        return TYPE_CONVERSIONS[index](address, name, provider)
    else:
        return None

class KonanHelperProvider(lldb.SBSyntheticValueProvider):

    def __init__(self, valobj):
        self._valobj = valobj
        # Can probably be in a global
        self._process = lldb.debugger.GetSelectedTarget().GetProcess()
        self._ptr = lldb_val_to_ptr(self._valobj)
        self._base_address = self._valobj.GetValueAsUnsigned()
        self._children_type_info = self._init_child_type_info()
        self._childvalues = [None for x in range(self.num_children())]

    def _init_child_type_info(self):
        return []

    def num_children(self):
        return len(self._children_type_info)

    def has_children(self):
        return self.num_children() > 0

    def _child_info(self, index):
        return self._children_type_info[index]

    def get_child_at_index(self, index):
        return self._read_value(index)

    def system_count_children(self):
        return int(evaluate("(int)Konan_DebugGetFieldCount({})".format(self._ptr)).GetValue())

    def _calc_offset(self, addr):
        return addr - self._base_address

    def _type_generator(self, index):
        if index == 0:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeVoid).GetPointerType()
        elif index == 1:
            return self._valobj.GetType()
        elif index == 2:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeChar)
        elif index == 3:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeShort)
        elif index == 4:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeInt)
        elif index == 5:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeLongLong)
        elif index == 6:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeFloat)
        elif index == 7:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeDouble)
        elif index == 8:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeVoid).GetPointerType()
        elif index == 9:
            return self._valobj.GetType().GetBasicType(lldb.eBasicTypeBool)
        else:
            return None

    def _child_type(self, index):
        return _child_type_global(self._ptr, index)

    def _children_type_address(self, index):
        return long(evaluate("(void *)Konan_DebugGetFieldAddress({}, {})".format(self._ptr, index)).GetValue(), 0)

    def _read_string(self, expr, error):
        return self._process.ReadCStringFromMemory(long(evaluate(expr).GetValue(), 0), 0x1000, error)

    def _read_value(self, index):
        result = self._childvalues[index]
        if result is None:
            if len(self._children_type_info) <= index:
                return None
            type_info = self._children_type_info[index]
            value_type = type_info.type
            address = self._base_address + type_info.offset
            result = _type_conversion(int(value_type), address, str(type_info.name), self)
            self._childvalues[index] = result
        return result

    def _create_synthetic_child(self, name):
        index = self.get_child_index(name)
        type_info = self._child_info(index)
        value = self._valobj.CreateChildAtOffset(str(name),
                                                 type_info.offset,
                                                 self._type_generator(type_info.type))

        value.SetSyntheticChildrenGenerated(True)
        value.SetPreferSyntheticValue(True)

        return value

class KonanStringSyntheticProvider:
    def __init__(self, valobj, type_check_result):
        buff_len = (type_check_result*-1) - STRING_SIZE_OFFSET

        if not buff_len:
            self._representation = valobj.GetValue()
            return

        process = lldb.debugger.GetSelectedTarget().GetProcess()
        error = lldb.SBError()
        s = process.ReadCStringFromMemory(debug_string_buffer_ptr(), int(buff_len), error)
        if not error.Success():
            raise DebuggerException()
        self._representation = s if error.Success() else valobj.GetValue()
        self._logger = lldb.formatters.Logger.Logger()

    def update(self):
        pass

    def num_children(self):
        return 0

    def has_children(self):
        return False

    def get_child_index(self, _):
        return None

    def get_child_at_index(self, _):
        return None

    def to_string(self):
        return self._representation

class DebuggerException(Exception):
    pass

TYPES_CACHE = {}

class KonanObjectSyntheticProvider(KonanHelperProvider):
    def __init__(self, valobj, tip):
        self._tip = tip
        super(KonanObjectSyntheticProvider, self).__init__(valobj)

    def _init_child_type_info(self):
        tip = self._tip
        ptr = self._ptr
        error = lldb.SBError()
        if tip > 0 and tip in TYPES_CACHE:
            return TYPES_CACHE[tip]
        else:
            kid_count = self.system_count_children()
            children_type_info = \
                [ChildMetaInfo(
                    self._read_string("(const char *)Konan_DebugGetFieldName({}, (int){})".format(ptr, x), error), _child_type_global(ptr, x), self._calc_offset(self._children_type_address(x))) for x in range(kid_count)]

            if tip != -1:
                TYPES_CACHE[tip] = children_type_info

            if not error.Success():
                raise DebuggerException()

            return children_type_info

    def get_child_index(self, name):
        for i in range(len(self._children_type_info)):
            if self._children_type_info[i].name == name:
                return i

        return -1

    def to_string(self):
        return ""

class ChildMetaInfo:
    def __init__(self, name, type, offset):
        self.name = name
        self.type = type
        self.offset = offset

#Cap array results to prevent slow response with large lists
MAX_VALUES = 20

class KonanArraySyntheticProvider(KonanHelperProvider):
    def __init__(self, valobj):
        super(KonanArraySyntheticProvider, self).__init__(valobj)
        if self._ptr is None:
            return
        valobj.SetSyntheticChildrenGenerated(True)

    def _init_child_type_info(self):

        # Calls to the underlying runtime are expensive. Arrays have a base address for entries
        # and a fixed size. We can determine that while looping through values. After the first 2
        # we have enough info to create the remaining entries

        child_count = min(self.system_count_children(), MAX_VALUES)
        target_address = self._valobj.GetValueAsUnsigned()
        array_type = 0
        array_base_address = 0
        array_type_size = 0
        entry_offset = 0
        result_list = []

        for x in range(child_count):
            if x == 0:
                array_type = self._child_type(x)
                array_base_address = self._children_type_address(x)
                entry_offset = array_base_address - target_address
            elif x == 1:
                first_address = self._children_type_address(x)
                array_type_size = first_address - array_base_address
            else:
                pass

            result_list.append(ChildMetaInfo(x, array_type, entry_offset + (x * array_type_size)))

        return result_list

    def get_child_index(self, name):
        index = int(name)
        return index if (0 <= index < self.num_children()) else -1

    def to_string(self):
        return [self.system_count_children()]

ARRAY_TYPE = -2
NO_TYPE_KNOWN = -3
STRING_SIZE_OFFSET = 10

class KonanProxyTypeProvider:
    def __init__(self, valobj, _):
        type_check_result = super_big_type_check(valobj)

        if type_check_result == NO_TYPE_KNOWN:
            return

        self._proxy = select_provider(valobj, type_check_result)
        self.update()

        self.update()

    def __getattr__(self, item):
        return getattr(self._proxy, item)

def print_this_command(debugger, command, result, internal_dict):
    pthis = lldb.frame.FindVariable('<this>')
    print(pthis)

def select_provider(lldb_val, type_check_result):
    return KonanStringSyntheticProvider(lldb_val, type_check_result) if type_check_result <= (-STRING_SIZE_OFFSET) else KonanArraySyntheticProvider(lldb_val) if type_check_result == ARRAY_TYPE else KonanObjectSyntheticProvider(lldb_val, type_check_result)

def __lldb_init_module(debugger, _):
    debugger.HandleCommand('\
        type summary add \
        --no-value \
        --expand \
        --python-function konan_lldb_fast.kotlin_object_type_summary \
        "struct ObjHeader *" \
        --category Kotlin\
    ')

    debugger.HandleCommand('\
        type synthetic add \
        --python-class konan_lldb_fast.KonanProxyTypeProvider\
        "ObjHeader *" \
        --category Kotlin\
    ')

    debugger.HandleCommand('type category enable Kotlin')
    debugger.HandleCommand('command script add -f {}.print_this_command print_this'.format(__name__))