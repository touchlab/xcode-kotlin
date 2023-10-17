package co.touchlab.xcode.cli.util

import co.touchlab.kermit.Logger
import kotlinx.cinterop.*
import platform.Foundation.NSArray
import platform.Foundation.NSData
import platform.Foundation.NSDate
import platform.Foundation.NSDictionary
import platform.Foundation.NSError
import platform.Foundation.NSMutableArray
import platform.Foundation.NSMutableDictionary
import platform.Foundation.NSNumber
import platform.Foundation.NSPropertyListBinaryFormat_v1_0
import platform.Foundation.NSPropertyListFormat
import platform.Foundation.NSPropertyListImmutable
import platform.Foundation.NSPropertyListOpenStepFormat
import platform.Foundation.NSPropertyListSerialization
import platform.Foundation.NSPropertyListXMLFormat_v1_0
import platform.Foundation.NSString
import platform.Foundation.create
import platform.Foundation.valueForKey
import platform.darwin.NSObject

@OptIn(ExperimentalForeignApi::class)
class PropertyList(val root: Object) {
    enum class Format {
        XML, OpenStep, Binary;

        val objc: NSPropertyListFormat
            get() = when (this) {
                XML -> NSPropertyListXMLFormat_v1_0
                OpenStep -> NSPropertyListOpenStepFormat
                Binary -> NSPropertyListBinaryFormat_v1_0
            }
    }
    sealed interface Object {
        val array: Array get() = this as Array
        val arrayOrNull: Array? get() = this as? Array
        val dictionary: Dictionary get() = this as Dictionary
        val dictionaryOrNull: Dictionary? get() = this as? Dictionary
        val string: String get() = this as String
        val stringOrNull: String? get() = this as? String
        val data: Data get() = this as Data
        val dataOrNull: Data? get() = this as? Data
        val date: Date get() = this as Date
        val dateOrNull: Date? get() = this as? Date
        val number: Number get() = this as Number
        val numberOrNull: Number? get() = this as? Number

        class Array(
            val items: MutableList<Object> = mutableListOf(),
        ): Object, MutableList<Object> by items

        class Dictionary(
            val items: MutableMap<kotlin.String, Object> = mutableMapOf(),
        ): Object, MutableMap<kotlin.String, Object> by items

        class String(
            val value: kotlin.String
        ): Object

        class Data(
            val value: NSData,
        ): Object

        class Date(
            val value: NSDate,
        ): Object

        class Number(
            val value: NSNumber
        ): Object
    }

    fun toData(format: Format = Format.Binary): NSData {
        return memScoped {
            val errorPointer: ObjCObjectVar<NSError?> = alloc()
            val data = NSPropertyListSerialization.dataWithPropertyList(
                plist = recursiveReverseBridge(root),
                format = format.objc,
                options = 0u,
                error = errorPointer.ptr,
            )
            val error = errorPointer.value
            if (error != null) {
                throw SerializationException(error)
            }
            checkNotNull(data) { "Serialized plist data were null even though error was null too. This should never happen!" }
        }
    }

    private fun recursiveReverseBridge(obj: Object): NSObject = when (obj) {
        is Object.Dictionary -> {
            val dictionary = NSMutableDictionary(capacity = obj.size.toULong())
            for ((key, value) in obj) {
                dictionary.setObject(recursiveReverseBridge(value), key.objc)
            }
            dictionary
        }
        is Object.Array -> {
            val array = NSMutableArray(capacity = obj.size.toULong())
            for (item in obj) {
                array.addObject(recursiveReverseBridge(item))
            }
            array
        }
        is Object.Data -> obj.value
        is Object.Date -> obj.value
        is Object.Number -> obj.value
        is Object.String -> obj.value.objc
    }

    class UnsupportedObjectTypeException(val nsObject: NSObject): Exception("Unsupported property list value: $nsObject")
    class DeserializationException(val error: NSError): Exception("Could not deserialize property list. Error: ${error.description}.")
    class SerializationException(val error: NSError): Exception("Could not serialize property list. Error: ${error.description}.")

    companion object {
        private val logger = Logger.withTag("PropertyList")

        fun create(path: Path): PropertyList {
            logger.v { "Loading property list from $path." }
            return create(File(path).dataContents())
        }

        fun create(file: File): PropertyList {
            logger.v { "Loading property list from file at ${file.path}" }
            return create(file.dataContents())
        }

        fun create(data: NSData): PropertyList {
            val rawPropertyList = memScoped {
                val errorPointer: ObjCObjectVar<NSError?> = alloc()
                val propertyList = NSPropertyListSerialization.propertyListWithData(
                    data = data,
                    options = NSPropertyListImmutable,
                    format = null,
                    error = errorPointer.ptr,
                )
                val error = errorPointer.value
                if (error != null) {
                    throw DeserializationException(error)
                }
                checkNotNull(propertyList) { "Deserialized plist was null even though error was null too. This should never happen!" }
            } as NSObject

            val root = recursiveBridge(rawPropertyList)
            return PropertyList(root)
        }

        private fun recursiveBridge(nsObject: NSObject): Object = when (nsObject) {
            is NSDictionary -> Object.Dictionary(
                nsObject.map { key, value -> key to recursiveBridge(value) }.toMutableMap()
            )
            is NSArray -> Object.Array(
                nsObject.map { item -> recursiveBridge(item) }.toMutableList()
            )
            is NSString -> Object.String(nsObject.kt)
            is NSData -> Object.Data(nsObject)
            is NSDate -> Object.Date(nsObject)
            is NSNumber -> Object.Number(nsObject)
            else -> throw UnsupportedObjectTypeException(nsObject)
        }

        private fun <T> NSArray.map(transform: (value: NSObject) -> T): List<T> {
            return (0UL until count).map { index ->
                transform(objectAtIndex(index) as NSObject)
            }
        }

        private fun <KEY, VALUE> NSDictionary.map(transform: (key: String, value: NSObject) -> Pair<KEY, VALUE>): Map<KEY, VALUE> {
            val result = mutableMapOf<KEY, VALUE>()
            val enumerator = keyEnumerator()
            while (true) {
                val nsKey = enumerator.nextObject() as String? ?: break
                val nsValue = valueForKey(nsKey) as NSObject? ?: continue

                val (key, value) = transform(nsKey, nsValue)
                result[key] = value
            }
            return result
        }
    }
}
