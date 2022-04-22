package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.Console
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
            val pluginInfo = PropertyList.create(pluginSourceInfoFile)
            return Version.fromString(pluginInfo.root.dictionary.getValue(pluginVersionInfoKey).string.value)
        }

    val installedVersion: Version?
        get() = if (pluginTargetFile.exists()) {
            val pluginInfo = PropertyList.create(pluginTargetInfoFile)
            pluginInfo.root.dictionaryOrNull?.get(pluginVersionInfoKey)?.stringOrNull?.value?.let(Version::fromString)
        } else {
            null
        }

    val isInstalled: Boolean
        get() = pluginTargetFile.exists()

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
        if (isInstalled) {
            Console.echo("Repairing plugin compatibility list.")
            val additionalPluginCompatibilityIds = xcodes.map { PropertyList.Object.String(it.pluginCompatabilityId) }
            val infoPlist = PropertyList.create(pluginTargetInfoFile)
            val rootDictionary = infoPlist.root.dictionary
            val oldPluginCompatibilityIds = rootDictionary
                .getOrPut(pluginCompatibilityInfoKey) { PropertyList.Object.Array(mutableListOf()) }
                .array
            oldPluginCompatibilityIds.addAll(additionalPluginCompatibilityIds)
            rootDictionary[pluginCompatibilityInfoKey] = PropertyList.Object.Array(
                oldPluginCompatibilityIds.distinctBy { it.stringOrNull?.value }.toMutableList()
            )
            pluginTargetInfoFile.write(infoPlist.toData(PropertyList.Format.XML))
        } else {
            Console.echo("Plugin not installed, nothing to repair.")
        }
    }

    fun uninstall() {
        pluginTargetFile.delete()
        XcodeHelper.removeKotlinPluginFromDefaults()
    }
}

