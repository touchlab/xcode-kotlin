#ifndef KONAN_DEBUG_H
#define KONAN_DEBUG_H

// This is true for K/N runtime that supports ObjC, so for our case it should always be 1.
#define KONAN_TYPE_INFO_HAS_WRITABLE_PART 1

#if KONAN_TYPE_INFO_HAS_WRITABLE_PART
struct WritableTypeInfo;
#endif

struct ObjHeader;
struct TypeInfo;

struct AssociatedObjectTableRecord {
  const TypeInfo* key;
  ObjHeader* (*getAssociatedObjectInstance)(ObjHeader**);
};

// Type for runtime representation of Konan object.
// Keep in sync with runtimeTypeMap in RTTIGenerator.
enum Konan_RuntimeType {
  RT_INVALID    = 0,
  RT_OBJECT     = 1,
  RT_INT8       = 2,
  RT_INT16      = 3,
  RT_INT32      = 4,
  RT_INT64      = 5,
  RT_FLOAT32    = 6,
  RT_FLOAT64    = 7,
  RT_NATIVE_PTR = 8,
  RT_BOOLEAN    = 9,
  RT_VECTOR128  = 10
};

// Flags per type.
// Keep in sync with constants in RTTIGenerator.
enum Konan_TypeFlags {
  TF_IMMUTABLE = 1 << 0,
  TF_ACYCLIC   = 1 << 1,
  TF_INTERFACE = 1 << 2,
  TF_OBJC_DYNAMIC = 1 << 3,
  TF_LEAK_DETECTOR_CANDIDATE = 1 << 4,
  TF_SUSPEND_FUNCTION = 1 << 5,
  TF_HAS_FINALIZER = 1 << 6,
  TF_HAS_FREEZE_HOOK = 1 << 7,
  TF_REFLECTION_SHOW_PKG_NAME = 1 << 8, // If package name is available in reflection, e.g. in `KClass.qualifiedName`.
  TF_REFLECTION_SHOW_REL_NAME = 1 << 9 // If relative name is available in reflection, e.g. in `KClass.simpleName`.
};

// Flags per object instance.
enum Konan_MetaFlags {
  // If freeze attempt happens on such an object - throw an exception.
  MF_NEVER_FROZEN = 1 << 0,
};


typedef signed char int8_t;
typedef unsigned char uint8_t;

typedef short int16_t;

typedef int int32_t;
typedef unsigned int uint32_t;

typedef long long int64_t;

typedef unsigned long uintptr_t;

// Extended information about a type.
struct ExtendedTypeInfo {
  // Number of fields (negated Konan_RuntimeType for array types).
  int32_t fieldsCount_;
  // Offsets of all fields.
  const int32_t* fieldOffsets_;
  // Types of all fields.
  const uint8_t* fieldTypes_;
  // Names of all fields.
  const char** fieldNames_;
  // Number of supported debug operations.
  int32_t debugOperationsCount_;
  // Table of supported debug operations functions.
  void** debugOperations_;
};

typedef void const* VTableElement;

typedef int32_t ClassId;

const ClassId kInvalidInterfaceId = 0;

struct InterfaceTableRecord {
    ClassId id;
    uint32_t vtableSize;
    VTableElement const* vtable;
};

// This struct represents runtime type information and by itself is the compile time
// constant.
// When adding a field here do not forget to adjust:
//   1. RTTIGenerator
//   2. ObjectTestSupport TypeInfoHolder
//   3. createTypeInfo in ObjcExport.mm
struct TypeInfo {
    // Reference to self, to allow simple obtaining TypeInfo via meta-object.
    const TypeInfo* typeInfo_;
    // Extended RTTI, to retain cross-version debuggability, since ABI version 5 shall always be at the second position.
    const ExtendedTypeInfo* extendedInfo_;
    // Unused field.
    uint32_t unused_;
    // Negative value marks array class/string, and it is negated element size.
    int32_t instanceSize_;
    // Must be pointer to Any for array classes, and null for Any.
    const TypeInfo* superType_;
    // All object reference fields inside this object.
    const int32_t* objOffsets_;
    // Count of object reference fields inside this object.
    // 1 for kotlin.Array to mark it as non-leaf.
    int32_t objOffsetsCount_;
    const TypeInfo* const* implementedInterfaces_;
    int32_t implementedInterfacesCount_;
    int32_t interfaceTableSize_;
    InterfaceTableRecord const* interfaceTable_;

    // String for the fully qualified dot-separated name of the package containing class.
    ObjHeader* packageName_;

    // String for the qualified class name relative to the containing package
    // (e.g. TopLevel.Nested1.Nested2) or the effective class name computed for
    // local class or anonymous object (e.g. listOf$1).
    ObjHeader* relativeName_;

    // Various flags.
    int32_t flags_;

    // Class id built with the whole class hierarchy taken into account. The details are in ClassLayoutBuilder.
    ClassId classId_;

#if KONAN_TYPE_INFO_HAS_WRITABLE_PART
    WritableTypeInfo* writableInfo_;
#endif

    // Null-terminated array.
    const AssociatedObjectTableRecord* associatedObjects;

    // Invoked on an object during mark phase.
    // TODO: Consider providing a generic traverse method instead.
    void (*processObjectInMark)(void*,ObjHeader*);

    // Required alignment of instance
    uint32_t instanceAlignment_;


    // vtable starts just after declared contents of the TypeInfo:
    // void* const vtable_[];
};

struct ObjHeader {
    TypeInfo* typeInfoOrMeta_;
};

// Header of value type array objects. Keep layout in sync with that of object header.
struct ArrayHeader {
    TypeInfo* typeInfoOrMeta_;

    // Elements count. Element size is stored in instanceSize_ field of TypeInfo, negated.
    uint32_t count_;
};

typedef void __konan_safe_void_t;
typedef int __konan_safe_int_t;
typedef char __konan_safe_char_t;
typedef bool __konan_safe_bool_t;
typedef float __konan_safe_float_t;
typedef double __konan_safe_double_t;

typedef struct MapEntry { ObjHeader* key; ObjHeader* value; } MapEntry;

int runtimeTypeSize[] = {
    -1,                  // INVALID
    sizeof(ObjHeader*),  // OBJECT
    1,                   // INT8
    2,                   // INT16
    4,                   // INT32
    8,                   // INT64
    4,                   // FLOAT32
    8,                   // FLOAT64
    sizeof(void*),       // NATIVE_PTR
    1,                   // BOOLEAN
    16                   // VECTOR128
};

int runtimeTypeAlignment[] = {
    -1,                  // INVALID
    alignof(ObjHeader*), // OBJECT
    alignof(int8_t),     // INT8
    alignof(int16_t),    // INT16
    alignof(int32_t),    // INT32
    alignof(int64_t),    // INT64
    alignof(float),      // FLOAT32
    alignof(double),     // FLOAT64
    alignof(void*),      // NATIVE_PTR
    1,                   // BOOLEAN
    16                   // VECTOR128
};

class BackRefFromAssociatedObject {
 public:
  union {
    void* ref_; // Regular object.
    ObjHeader* permanentObj_; // Permanent object.
  };
};

#endif // KONAN_DEBUG_H
