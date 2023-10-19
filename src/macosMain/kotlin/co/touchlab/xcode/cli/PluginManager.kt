package co.touchlab.xcode.cli

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.util.*
import platform.posix.sleep

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
    private val fixXcode15Timeout = 10

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

    fun install() {
        logger.v { "Ensuring plugins directory exists at ${pluginsDirectory.path}" }
        pluginsDirectory.mkdirs()
        logger.v { "Copying Xcode plugin to target path ${pluginTargetFile.path}" }
        pluginSourceFile.copy(pluginTargetFile.path)
    }

    fun enable(version: Version, xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        logger.i { "Removing Kotlin Plugin defaults so we can add it to allowed." }
        XcodeHelper.removeKotlinPluginFromDefaults()
        logger.i { "Allowing Kotlin Plugin" }
        XcodeHelper.allowKotlinPlugin(version, xcodeInstallations)
    }

    fun disable(version: Version, xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        logger.i { "Removing Kotlin Plugin defaults so we can add it to skipped." }
        XcodeHelper.removeKotlinPluginFromDefaults()
        logger.i { "We need Xcode to skip the plugin, so it doesn't crash." }
        XcodeHelper.skipKotlinPlugin(version, xcodeInstallations)
    }

    fun sync(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        check(isInstalled) { "Plugin is not installed!" }

        Console.echo("Synchronizing plugin compatibility list.")
        val additionalPluginCompatibilityIds =
            xcodeInstallations.map { PropertyList.Object.String(it.pluginCompatabilityId) }
        logger.v { "Xcode installation IDs to include: ${additionalPluginCompatibilityIds.joinToString { it.value }}" }
        val infoPlist = PropertyList.create(pluginTargetInfoFile)
        val rootDictionary = infoPlist.root.dictionary
        val oldPluginCompatibilityIds = rootDictionary
            .getOrPut(pluginCompatibilityInfoKey) { PropertyList.Object.Array(mutableListOf()) }
            .array
        logger.v {
            "Previous Xcode installation IDs: ${
                oldPluginCompatibilityIds.mapNotNull { it.stringOrNull?.value }.joinToString()
            }"
        }
        oldPluginCompatibilityIds.addAll(additionalPluginCompatibilityIds)
        val distinctPluginCompatibilityIds =
            oldPluginCompatibilityIds.distinctBy { it.stringOrNull?.value }.toMutableList()
        logger.v {
            "Xcode installation IDs to save: ${
                distinctPluginCompatibilityIds.mapNotNull { it.stringOrNull?.value }.joinToString()
            }"
        }
        rootDictionary[pluginCompatibilityInfoKey] = PropertyList.Object.Array(distinctPluginCompatibilityIds)
        pluginTargetInfoFile.write(infoPlist.toData(PropertyList.Format.XML))
    }

    fun uninstall() {
        logger.i { "Deleting Xcode plugin from ${pluginTargetFile.path}" }
        pluginTargetFile.delete()
        XcodeHelper.removeKotlinPluginFromDefaults()
    }

    fun fixXcode15(xcodeInstallations: List<XcodeHelper.XcodeInstallation>): Unit = try {
        val cacheDir = Path(Shell.exec("/usr/bin/getconf", "DARWIN_USER_CACHE_DIR").output.orEmpty().trim())
        logger.i { "Enabling IDEPerformanceDebugger built-in plugin." }
        XcodeHelper.setIDEPerformanceDebuggerEnabled(true)

        xcodeInstallations
            .filter { it.version.startsWith("15.") }
            .forEach { installation ->
                logger.i { "Opening ${installation.name} in background to generate plugin cache" }
                XcodeHelper.openInBackground(installation)

                try {
                    for (i in 1..fixXcode15Timeout) {
                        sleep(1u)

                        val pluginCachePath =
                            cacheDir / "com.apple.DeveloperTools" / "${installation.version}-${installation.build}" / "Xcode" / "PlugInCache-Debug.xcplugincache"

                        if (pluginCachePath.exists()) {
                            logger.i { "${installation.name} plugin cache file exists, checking if it contains IDEPerformanceDebugger entry yet" }
                            val pluginCache = PropertyList.create(pluginCachePath)
                            val containsIDEPerformanceDebuggerInfo = with(XcodeHelper.PlugInCache) {
                                pluginCache.scanRecords.contains { record ->
                                    record.bundlePath.endsWith("IDEPerformanceDebugger.framework")
                                }
                            }

                            if (containsIDEPerformanceDebuggerInfo) {
                                // Xcode updated the cache and should work now, we're done.
                                logger.i { "${installation.name} updated the plugin cache and should work now." }
                                break
                            } else {
                                logger.i { "${installation.name} plugin cache doesn't contain IDEPerformanceDebugger entry yet." }
                            }
                        } else {
                            logger.i { "${installation.name} plugin cache file doesn't exist yet." }
                        }

                        if (i == fixXcode15Timeout) {
                            error("IDEPerformanceDebugger.framework was not found in ${installation.name} plugin cache after waiting $fixXcode15Timeout seconds. Please try again, or report an issue in the xcode-kotlin repository.")
                        }
                    }
                } finally {
                    logger.i { "Killing ${installation.name}" }
                    XcodeHelper.killRunningXcode().checkSuccessful {
                        "Couldn't shut down Xcode!"
                    }
                }
            }
    } finally {
        logger.i { "Disabling IDEPerformanceDebugger built-in plugin." }
        XcodeHelper.setIDEPerformanceDebuggerEnabled(false)
    }
}
