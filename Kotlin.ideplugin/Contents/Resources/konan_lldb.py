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

def _read_string_dispose_global(process, expr, disp_expr, error):
    str_ptr = long(evaluate(expr).GetValue(), 0)
    read_string = process.ReadCStringFromMemory(str_ptr, 0x1000, error)
    evaluate(disp_expr.format(str_ptr))
    return read_string

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

def _child_type_global(ptr, index):
    return evaluate("(int)Konan_DebugGetFieldType({}, {})".format(ptr, index)).GetValueAsUnsigned()

def _children_type_address_global(ptr, index):
    return long(evaluate("(void *)Konan_DebugGetFieldAddress({}, {})".format(ptr, index)).GetValue(), 0)

def system_count_children_global(ptr):
    return int(evaluate("(int)Konan_DebugGetFieldCount({})".format(ptr)).GetValue())

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
        return system_count_children_global(self._ptr)

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
        return _child_type_global(self._ptr, index)

    def _children_type_address(self, index):
        return _children_type_address_global(self._ptr, index)

    def _read_string(self, expr, error):
        return self._process.ReadCStringFromMemory(long(evaluate(expr).GetValue(), 0), 0x1000, error)

    def _read_string_dispose(self, expr, disp_expr, error):
        return _read_string_dispose_global(self._process, expr, disp_expr, error)

    def _read_value(self, index):
        result = self._childvalues[index]
        if result is None:
            if len(self._children_type_info) <= index:
                return None
            type_info = self._children_type_info[index]
            value_type = type_info.type
            address = self._base_address + type_info.offset
            result = self._type_convesion_lamb(int(value_type))(address, str(type_info.name))
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

    def _init_child_type_info(self):
        tip = type_info_ptr(self._valobj)
        ptr = self._ptr
        error = lldb.SBError()
        if tip != -1 and tip in TYPES_CACHE:
            return TYPES_CACHE[tip]
        else:
            kid_count = system_count_children_global(ptr)
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

#Cap array results to prevent super slow response
MAX_VALUES = 20

class KonanArraySyntheticProvider(KonanHelperProvider):
    def __init__(self, valobj):
        super(KonanArraySyntheticProvider, self).__init__(valobj)
        if self._ptr is None:
            return
        valobj.SetSyntheticChildrenGenerated(True)

    def _init_child_type_info(self):
        child_count = min(self.system_count_children(), MAX_VALUES)
        return [ChildMetaInfo(x, self._child_type(x), self._calc_offset(self._children_type_address(x))) for x in range(child_count)]

    def get_child_index(self, name):
        index = int(name)
        return index if (0 <= index < self.num_children()) else -1

    def to_string(self):
        return [self.system_count_children()]

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

def select_provider(lldb_val):
    if is_string(lldb_val):
        return KonanStringSyntheticProvider(lldb_val)
    elif is_array(lldb_val):
        return KonanArraySyntheticProvider(lldb_val)
    else:
        tip = type_info_ptr(lldb_val)
        cnError = lldb.SBError()
        classNameSummary = str(_read_string_dispose_global(lldb.debugger.GetSelectedTarget().GetProcess(), "(const char *)XcodeKotlin_className({})".format(tip), "XcodeKotlin_disposeString({})", cnError))

        ctfIndex = len(CUSTOM_TYPE_FACTORY) - 1

        while ctfIndex >= 0:
            ctf = CUSTOM_TYPE_FACTORY[ctfIndex]
            if ctf.matcher(classNameSummary):
                return ctf.factory(lldb_val)
            ctfIndex = ctfIndex - 1

CUSTOM_TYPE_FACTORY = []

class CustomTypeFactory:
    def __init__(self, matcher, factory):
        self.matcher = matcher
        self.factory = factory

class KonanAtomicReferenceSyntheticProvider(KonanObjectSyntheticProvider):
    def __init__(self, valobj):
        super(KonanAtomicReferenceSyntheticProvider, self).__init__(valobj)
        print "Making atref 222"

def _make_atomic_ref(lldb_val):
    return KonanAtomicReferenceSyntheticProvider(lldb_val)

def __lldb_init_module(debugger, _):
    CUSTOM_TYPE_FACTORY.append(
        CustomTypeFactory(
            lambda className: True,
            lambda x: KonanObjectSyntheticProvider(x)
        ))

    CUSTOM_TYPE_FACTORY.append(
        CustomTypeFactory(
            lambda className: className == "kotlin.native.concurrent.AtomicReference",
            _make_atomic_ref
        ))
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
