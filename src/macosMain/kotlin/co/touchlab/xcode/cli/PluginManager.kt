package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.PropertyList
import platform.Foundation.NSFileManager

object PluginManager {
    val pluginName = "Kotlin.ideplugin"
    val pluginSourcePath = Path.dataDir / pluginName
    val pluginTargetPath = XcodeHelper.xcodeLibraryPath / "Plug-ins" / pluginName

    val isInstalled: Boolean
        get() = NSFileManager.defaultManager.fileExistsAtPath(pluginTargetPath.value)

    val bundledVersion: String
        get() {
            val pluginInfo = PropertyList.create(pluginSourcePath / "Contents" / "Info.plist") ?: TODO("ERROR")
            return pluginInfo.root.dictionary.getValue("CFBundleVersion").string.value
        }

    val installedVersion: String?
        get() {
            val pluginInfo = PropertyList.create(pluginTargetPath / "Contents" / "Info.plist") ?: return null
            return pluginInfo.root.dictionaryOrNull?.get("CFBundleVersion")?.stringOrNull?.value
        }
}