package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.PropertyList
import co.touchlab.xcode.cli.util.Version
import co.touchlab.xcode.cli.util.fromString

object PluginManager {
    val pluginName = "Kotlin.ideplugin"
    val pluginSourceFile = File(Path.dataDir / pluginName)
    val pluginTargetFile = File(XcodeHelper.xcodeLibraryPath / "Plug-ins" / pluginName)

    private val pluginSourceInfoFile = File(pluginSourceFile.path / "Contents" / "Info.plist")
    private val pluginTargetInfoFile = File(pluginTargetFile.path / "Contents" / "Info.plist")
    private val pluginVersionInfoKey = "CFBundleShortVersionString"
    private val pluginCompatibilityInfoKey = "DVTPlugInCompatibilityUUIDs"

    val bundledVersion: Version
        get() {
            val pluginInfo = PropertyList.create(pluginSourceInfoFile) ?: TODO("ERROR")
            return Version.fromString(pluginInfo.root.dictionary.getValue(pluginVersionInfoKey).string.value)
        }

    val installedVersion: Version?
        get() = if (pluginTargetFile.exists()) {
            val pluginInfo = PropertyList.create(pluginTargetInfoFile)
            pluginInfo.root.dictionaryOrNull?.get(pluginVersionInfoKey)?.stringOrNull?.value?.let(Version::fromString)
        } else {
            null
        }

    val targetSupportedXcodeUUIds: List<String>
        get() = if (pluginTargetFile.exists()) {
            PropertyList.create(pluginTargetInfoFile)
                .root
                .dictionaryOrNull
                ?.get(pluginCompatibilityInfoKey)
                ?.arrayOrNull
                ?.mapNotNull { it.stringOrNull?.value }
                ?: emptyList()
        } else {
            emptyList()
        }

    fun install(xcodes: List<XcodeHelper.XcodeInstallation>) {
        // Copy plugin
        pluginSourceFile.copy(pluginTargetFile.path)
        // Repair plugin
        repair(xcodes)
    }

    fun repair(xcodes: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.removeKotlinPluginFromDefaults()
        val pluginCompatibilityIds = xcodes.map { it.pluginCompatabilityId }
        val infoPlist = PropertyList.create(pluginTargetInfoFile)
        infoPlist.root.dictionary.getOrPut(pluginCompatibilityInfoKey) { PropertyList.Object.Array(mutableListOf()) }
            .array.addAll(pluginCompatibilityIds.map { PropertyList.Object.String(it) })
        pluginTargetInfoFile.write(infoPlist.toData(PropertyList.Format.XML))
    }

    fun uninstall() {
        pluginTargetFile.delete()
        XcodeHelper.removeKotlinPluginFromDefaults()
    }
}

