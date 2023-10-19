package co.touchlab.xcode.cli.util

import platform.Foundation.NSBundle
import platform.Foundation.NSFileManager
import platform.Foundation.NSHomeDirectory
import platform.Foundation.NSString
import platform.Foundation.stringByAppendingPathComponent
import platform.Foundation.stringByDeletingLastPathComponent
import platform.Foundation.stringByResolvingSymlinksInPath

data class Path(
    val value: String,
) {
    val parent: Path
        get() = deletingLastPathComponent()

    constructor(basePath: Path, vararg components: String): this(basePath.value, *components)

    constructor(basePath: String, vararg components: String): this(components.fold(basePath) { path, component ->
        path.appendingPathComponent(component)
    })

    operator fun div(component: String): Path {
        return appendingPathComponent(component)
    }

    fun appendingPathComponent(component: String): Path {
        return Path(value.appendingPathComponent(component))
    }

    fun deletingLastPathComponent(): Path {
        return Path(value.deletingLastPathComponent())
    }

    fun resolvingSymlinksInPath(): Path {
        return Path(value.resolvingSymlinksInPath())
    }

    fun exists(): Boolean = NSFileManager.defaultManager.fileExistsAtPath(value)

    override fun toString(): String {
        return value
    }

    companion object {
        val home: Path
            get() = Path(NSHomeDirectory())

        val workDir: Path
            get() = Path(NSFileManager.defaultManager.currentDirectoryPath)

        val binaryDir: Path
            get() = Path(NSBundle.mainBundle.bundlePath)

        val dataDir: Path
            get() = if (Platform.isDebugBinary) {
                // TODO: This requires running the debug binary with working directory set to the project's root after running `./gradlew preparePlugin`.
                workDir / "build" / "share"
            } else {
                // TODO: This will only be true when installing through Homebrew. Do we want to have different configurations?
                binaryDir.parent / "share"
            }

        private fun String.appendingPathComponent(component: String): String {
            return this.objc.stringByAppendingPathComponent(component)
        }

        private fun String.deletingLastPathComponent(): String {
            return this.objc.stringByDeletingLastPathComponent()
        }

        private fun String.resolvingSymlinksInPath(): String {
            return this.objc.stringByResolvingSymlinksInPath()
        }
    }
}
