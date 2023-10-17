package co.touchlab.xcode.cli.util

import co.touchlab.xcode.cli.LLDBInitManager
import kotlinx.cinterop.*
import platform.Foundation.NSData
import platform.Foundation.NSDataWritingAtomic
import platform.Foundation.NSError
import platform.Foundation.NSFileManager
import platform.Foundation.NSString
import platform.Foundation.NSUTF8StringEncoding
import platform.Foundation.create
import platform.Foundation.writeToFile

@OptIn(ExperimentalForeignApi::class)
class File(private val providedPath: Path, private val resolveSymlinks: Boolean = true) {
    val path: Path
        get() = if (resolveSymlinks) {
            providedPath.resolvingSymlinksInPath()
        } else {
            providedPath
        }

    fun dataContents(): NSData = throwingIOException { errorPointer ->
        NSData.create(contentsOfFile = path.value, options = 0u, error = errorPointer.ptr)
    } ?: error("Couldn't load data contents of file $path. This shouldn't have been thrown, because we should receive a NSError!")

    fun stringContents(): NSString = throwingIOException { errorPointer ->
        NSString.create(contentsOfFile = path.value, encoding = NSUTF8StringEncoding, error = errorPointer.ptr)
    } ?: error("Couldn't load UTF8 content of file $path. This shouldn't have been thrown, because we should receive a NSError!")

    fun exists(): Boolean = NSFileManager.defaultManager.fileExistsAtPath(path.value)

    fun write(data: NSData): Boolean = throwingIOException { errorPointer ->
        data.writeToFile(path.value, options = NSDataWritingAtomic, error = errorPointer.ptr)
    }

    fun write(string: NSString): Boolean = throwingIOException { errorPointer ->
        string.writeToFile(path.value, true, NSUTF8StringEncoding, errorPointer.ptr)
    }

    fun copy(destination: Path): Boolean = throwingIOException { errorPointer ->
        NSFileManager.defaultManager.copyItemAtPath(path.value, destination.value, errorPointer.ptr)
    }

    fun mkdirs(): Boolean = throwingIOException { errorPointer ->
        NSFileManager.defaultManager.createDirectoryAtPath(path.value, true, null, errorPointer.ptr)
    }

    fun delete(): Boolean {
        if (!exists()) {
            return false
        }
        return throwingIOException { errorPointer ->
            NSFileManager.defaultManager.removeItemAtPath(path.value, errorPointer.ptr)
        }
    }

    override fun toString(): String {
        return "File($path)"
    }

    private inline fun <T> throwingIOException(crossinline block: (ObjCObjectVar<NSError?>) -> T): T {
        return memScoped {
            val errorPointer: ObjCObjectVar<NSError?> = alloc()
            val result = block(errorPointer)
            val error = errorPointer.value
            if (error != null) {
                throw IOException(error)
            }
            result
        }
    }

    class IOException(val nsError: NSError): Exception(nsError.description)
}
