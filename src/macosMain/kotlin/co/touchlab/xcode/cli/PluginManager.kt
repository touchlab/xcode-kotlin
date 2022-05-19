package co.touchlab.xcode.cli

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.PropertyList
import co.touchlab.xcode.cli.util.Version
import co.touchlab.xcode.cli.util.fromString

object PluginManager {
    val pluginName = "Kotlin.ideplugin"
    val pluginSourceFile = File(Path.dataDir / pluginName)
    val pluginsDirectory = File(XcodeHelper.xcodeLibraryPath / "Plug-ins")
    val pluginTargetFile = File(pluginsDirectory.path / pluginName)

    private val pluginSourceInfoFile = File(pluginSourceFile.path / "Contents" / "Info.plist")
    private val pluginTargetInfoFile = File(pluginTargetFile.path / "Contents" / "Info.plist")
    private val pluginVersionInfoKey = "CFBundleShortVersionString"
    private val pluginCompatibilityInfoKey = "DVTPlugInCompatibilityUUIDs"
    private val logger = Logger.withTag("PluginManager")

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

    fun install(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        logger.v { "Ensuring plugins directory exists at ${pluginsDirectory.path}" }
        pluginsDirectory.mkdirs()
        logger.v { "Copying Xcode plugin to target path ${pluginTargetFile.path}" }
        pluginSourceFile.copy(pluginTargetFile.path)
        sync(xcodeInstallations)
    }

    fun sync(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.removeKotlinPluginFromDefaults()
        if (isInstalled) {
            XcodeHelper.addKotlinPluginToDefaults(installedVersion ?: bundledVersion, xcodeInstallations)
            Console.echo("Synchronizing plugin compatibility list.")
            val additionalPluginCompatibilityIds = xcodeInstallations.map { PropertyList.Object.String(it.pluginCompatabilityId) }
            logger.v { "Xcode installation IDs to include: ${additionalPluginCompatibilityIds.joinToString { it.value }}" }
            val infoPlist = PropertyList.create(pluginTargetInfoFile)
            val rootDictionary = infoPlist.root.dictionary
            val oldPluginCompatibilityIds = rootDictionary
                .getOrPut(pluginCompatibilityInfoKey) { PropertyList.Object.Array(mutableListOf()) }
                .array
            logger.v { "Previous Xcode installation IDs: ${oldPluginCompatibilityIds.mapNotNull { it.stringOrNull?.value }.joinToString()}" }
            oldPluginCompatibilityIds.addAll(additionalPluginCompatibilityIds)
            val distinctPluginCompatibilityIds = oldPluginCompatibilityIds.distinctBy { it.stringOrNull?.value }.toMutableList()
            logger.v { "Xcode installation IDs to save: ${distinctPluginCompatibilityIds.mapNotNull { it.stringOrNull?.value }.joinToString()}" }
            rootDictionary[pluginCompatibilityInfoKey] = PropertyList.Object.Array(distinctPluginCompatibilityIds)
            pluginTargetInfoFile.write(infoPlist.toData(PropertyList.Format.XML))
        } else {
            Console.echo("Plugin not installed, nothing to synchronize.")
        }
    }

    fun uninstall() {
        logger.i { "Deleting Xcode plugin from ${pluginTargetFile.path}" }
        pluginTargetFile.delete()
        XcodeHelper.removeKotlinPluginFromDefaults()
    }
}

