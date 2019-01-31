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

TYPE_INFO_REF = "*(void **)((uintptr_t)(*(void**){0}) & ~0x3)"
TYPE_INFO_DOUBLE_REF = "**(void***)((uintptr_t)(*(void**){0}) & ~0x3)"

def type_info_ptr(value):
    #This will be done when creating the proxy, so we don't need to repeat. Would be nice to have tests...
    # if not check_type_info(value):
    #     return -1

    expr = "*(void **)((uintptr_t)(*(void**){0}) & ~0x3)".format(value.unsigned)
    result = evaluate(expr)
    if result.IsValid():
        return result.GetValue()
    else:
        return -1

def evaluate(expr):
    return lldb.debugger.GetSelectedTarget().EvaluateExpression(expr, lldb.SBExpressionOptions())


def is_instance_of(addr, typeinfo):
    return evaluate("(bool)IsInstance({}, {})".format(addr, typeinfo)).GetValue() == "true"


def is_string(value):
    return is_instance_of(lldb_val_to_ptr(value), "theStringTypeInfo")


def is_array(value):
    return int(evaluate("(int)Konan_DebugIsArray({})".format(lldb_val_to_ptr(value))).GetValue()) == 1


def check_type_info(value):
    """This method checks self-referencing of pointer of first member of TypeInfo including case when object has an
    meta-object pointed by TypeInfo. Two lower bits are reserved for memory management needs see runtime/src/main/cpp/Memory.h."""
    if str(value.type) != "struct ObjHeader *":
        return False
    expr = (TYPE_INFO_REF + " == "+ TYPE_INFO_DOUBLE_REF).format(value.unsigned)
    result = evaluate(expr)
    return result.IsValid() and result.GetValue() == "true"


#
# Some kind of forward declaration.


__FACTORY = {}


def kotlin_object_type_summary(lldb_val, internal_dict):
    """Hook that is run by lldb to display a Kotlin object."""
    fallback = lldb_val.GetValue()
    if str(lldb_val.type) != "struct ObjHeader *":
        return fallback

    if not check_type_info(lldb_val):
        return NULL

    ptr = lldb_val_to_ptr(lldb_val)
    if ptr is None:
        return fallback

    return select_provider(lldb_val).to_string()


def select_provider(lldb_val):
    return __FACTORY['string'](lldb_val) if is_string(lldb_val) else __FACTORY['array'](lldb_val) if is_array(
        lldb_val) else __FACTORY['object'](lldb_val)

class KonanHelperProvider(lldb.SBSyntheticValueProvider):

    def __init__(self, valobj):
        self._valobj = valobj
        self._target = lldb.debugger.GetSelectedTarget()
        self._process = self._target.GetProcess()
        self._ptr = lldb_val_to_ptr(self._valobj)
        self._children_count = int(evaluate("(int)Konan_DebugGetFieldCount({})".format(self._ptr)).GetValue())
        self._children_type_info = []
        self._childvalues = [None for x in range(self.num_children())]

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

    def _type_convesion_lamb(self, index):
        if index == 0:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(void *){:#x}".format(address))
        elif index == 1:
            return lambda address, name: self._create_synthetic_child(name)
        elif index == 2:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(int8_t *){:#x}".format(address))
        elif index == 3:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(int16_t *){:#x}".format(address))
        elif index == 4:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(int32_t *){:#x}".format(address))
        elif index == 5:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(int64_t *){:#x}".format(address))
        elif index == 6:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(float *){:#x}".format(address))
        elif index == 7:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(double *){:#x}".format(address))
        elif index == 8:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(void **){:#x}".format(address))
        elif index == 9:
            return lambda address, name: self._valobj.CreateValueFromExpression(name, "(bool *){:#x}".format(address))
        elif index == 10:
            return lambda address, name: None
        else:
            return None

    def _child_type(self, index):
        return evaluate("(int)Konan_DebugGetFieldType({}, {})".format(self._ptr, index)).GetValueAsUnsigned()

    def _children_type_address(self, index):
        return long(evaluate("(void *)Konan_DebugGetFieldAddress({}, {})".format(self._ptr, index)).GetValue(), 0)

    def _read_string(self, expr, error):
        return self._process.ReadCStringFromMemory(long(evaluate(expr).GetValue(), 0), 0x1000, error)

    def _read_value(self, index):
        result = self._childvalues[index]
        if result is None:
            type_info = self._children_type_info[index]
            value_type = type_info.type
            address = type_info.address
            result = self._type_convesion_lamb(int(value_type))(address, str(type_info.name))
            self._childvalues[index] = result
        return result

    def _create_synthetic_child(self, name):
        index = self.get_child_index(name)
        value = self._valobj.CreateChildAtOffset(str(name),
                                                 self._children_type_address(index) - self._valobj.GetValueAsUnsigned(),
                                                 self._read_type(index))
        value.SetSyntheticChildrenGenerated(True)
        value.SetPreferSyntheticValue(True)
        return value

    def _read_type(self, index):
        return self._type_generator(int(evaluate("(int)Konan_DebugGetFieldType({}, {})".format(self._ptr, index)).GetValue()))

    def _deref_or_obj_summary(self, index):
        value = self._read_value(index)
        if not value:
            print("_deref_or_obj_summary: value none, index:{}, type:{}".format(index, self._child_type(index)))
            return None
        if check_type_info(value.unsigned):
            return ""
        else:
            return kotlin_object_type_summary(value.deref, None)

class KonanStringSyntheticProvider:
    def __init__(self, valobj):
        ptr = lldb_val_to_ptr(valobj)
        fallback = valobj.GetValue()
        buff_len = evaluate(
            '(int)Konan_DebugObjectToUtf8Array({}, (char *)Konan_DebugBuffer(), (int)Konan_DebugBufferSize());'.format(
                ptr)
        ).unsigned

        if not buff_len:
            self._representation = fallback
            return

        process = lldb.debugger.GetSelectedTarget().GetProcess()

        buff_addr = evaluate("(char *)Konan_DebugBuffer()").unsigned

        error = lldb.SBError()
        s = process.ReadCStringFromMemory(long(buff_addr), int(buff_len), error)
        if not error.Success():
            raise DebuggerException()
        self._representation = s if error.Success() else fallback
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
    def __init__(self, valobj):
        super(KonanObjectSyntheticProvider, self).__init__(valobj)
        error = lldb.SBError()
        tip = type_info_ptr(valobj)
        if tip != -1 and tip in TYPES_CACHE:
            # print "cached "+ str(tip)
            self._children_type_info = TYPES_CACHE[tip]
        else:
            # print "Pointer: "+ str(tip)
            # print "Typename: "+ self._read_string("CreateCStringFromString(((TypeInfo*){})->relativeName_)".format(tip), error)
            self._children_type_info = \
            [ChildMetaInfo(
                self._read_string("(const char *)Konan_DebugGetFieldName({}, (int){})".format(self._ptr, x), error), self._child_type(x), self._children_type_address(x)) for x in range(self._children_count)]
            if tip != -1:
                TYPES_CACHE[tip] = self._children_type_info

        if not error.Success():
            raise DebuggerException()

    def num_children(self):
        return self._children_count

    def has_children(self):
        return self._children_count > 0

    def get_child_index(self, name):
        for i in range(len(self._children_type_info)):
            if self._children_type_info[i].name == name:
                return i

        return -1

    def get_child_at_index(self, index):
        return self._read_value(index)

    def to_string(self):
        return ""

class ChildMetaInfo:
    def __init__(self, name, type, address):
        self.name = name
        self.type = type
        self.address = address

#Cap array results to prevent super slow response
MAX_VALUES = 20

class KonanArraySyntheticProvider(KonanHelperProvider):
    def __init__(self, valobj):
        super(KonanArraySyntheticProvider, self).__init__(valobj)
        if self._ptr is None:
            return
        valobj.SetSyntheticChildrenGenerated(True)
        self._children_type_info = [ChildMetaInfo(x, self._child_type(x), self._children_type_address(x)) for x in range(self.num_children())]
        # self._children = [x for x in range(self.num_children())]

    def num_children(self):
        return min(self._children_count, MAX_VALUES)

    def has_children(self):
        return self._children_count > 0

    def get_child_index(self, name):
        index = int(name)
        return index if (0 <= index < self.num_children()) else -1

    def get_child_at_index(self, index):
        return self._read_value(index)

    def to_string(self):
        return [self._children_count]


class KonanProxyTypeProvider:
    def __init__(self, valobj, _):
        if not check_type_info(valobj):
            return
        self._proxy = select_provider(valobj)
        self.update()

    def __getattr__(self, item):
        return getattr(self._proxy, item)

def print_this_command(debugger, command, result, internal_dict):
    pthis = lldb.frame.FindVariable('<this>')
    print(pthis)

def __lldb_init_module(debugger, _):
    __FACTORY['object'] = lambda x: KonanObjectSyntheticProvider(x)
    __FACTORY['array'] = lambda x: KonanArraySyntheticProvider(x)
    __FACTORY['string'] = lambda x: KonanStringSyntheticProvider(x)
    debugger.HandleCommand('\
        type summary add \
        --no-value \
        --expand \
        --python-function konan_lldb.kotlin_object_type_summary \
        "struct ObjHeader *" \
        --category Kotlin\
    ')
    debugger.HandleCommand('\
        type synthetic add \
        --python-class konan_lldb.KonanProxyTypeProvider\
        "ObjHeader *" \
        --category Kotlin\
    ')
    debugger.HandleCommand('type category enable Kotlin')
    debugger.HandleCommand('command script add -f {}.print_this_command print_this'.format(__name__))
