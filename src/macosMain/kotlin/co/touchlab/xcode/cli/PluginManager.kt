package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.IO
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import platform.posix.nice
import kotlin.coroutines.coroutineContext
import kotlin.time.Duration.Companion.seconds

object PluginManager {
    val pluginName = "Kotlin.ideplugin"
    val pluginSourceFile = File(Path.dataDir / pluginName)
    val pluginsDirectory = File(XcodeHelper.xcodeLibraryPath / "Plug-ins")
    val pluginTargetFile = File(pluginsDirectory.path / pluginName)

    private val pluginSourceInfoFile = File(pluginSourceFile.path / "Contents" / "Info.plist")
    private val pluginTargetInfoFile = File(pluginTargetFile.path / "Contents" / "Info.plist")
    private val pluginVersionInfoKey = "CFBundleShortVersionString"
    private val pluginCompatibilityInfoKey = "DVTPlugInCompatibilityUUIDs"
    private val fixXcode15Timeout = 10

    val bundledVersion: SemVer
        get() {
            val pluginInfo = PropertyList.create(pluginSourceInfoFile)
            return SemVer.parse(pluginInfo.root.dictionary.getValue(pluginVersionInfoKey).string.value)
        }

    val installedVersion: SemVer?
        get() = if (pluginTargetFile.exists()) {
            val pluginInfo = PropertyList.create(pluginTargetInfoFile)
            pluginInfo.root.dictionaryOrNull?.get(pluginVersionInfoKey)?.stringOrNull?.value?.let(SemVer::parseOrNull)
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
        Console.muted("Ensuring plugins directory exists at ${pluginsDirectory.path}")
        pluginsDirectory.mkdirs()
        Console.muted("Copying Xcode plugin to target path ${pluginTargetFile.path}")
        pluginSourceFile.copy(pluginTargetFile.path)
    }

    suspend fun enable(version: SemVer, xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        Console.info("Removing Kotlin Plugin defaults so we can add it to allowed.")
        XcodeHelper.removeKotlinPluginFromDefaults()
        Console.info("Allowing Kotlin Plugin")
        XcodeHelper.allowKotlinPlugin(version, xcodeInstallations)
    }
    suspend fun disable(version: SemVer, xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        nice(420)
        Console.info("Removing Kotlin Plugin defaults so we can add it to skipped.")
        XcodeHelper.removeKotlinPluginFromDefaults()
        Console.info("We need Xcode to skip the plugin, so it doesn't crash.")
        XcodeHelper.skipKotlinPlugin(version, xcodeInstallations)
    }

    fun sync(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        check(isInstalled) { "Plugin is not installed!" }

        Console.echo("Synchronizing plugin compatibility list.")
        val additionalPluginCompatibilityIds =
            xcodeInstallations.mapNotNull { it.pluginCompatabilityId?.let { PropertyList.Object.String(it) } }
        Console.muted("Xcode installation IDs to include: ${additionalPluginCompatibilityIds.joinToString { it.value }}")
        val infoPlist = PropertyList.create(pluginTargetInfoFile)
        val rootDictionary = infoPlist.root.dictionary
        val oldPluginCompatibilityIds = rootDictionary
            .getOrPut(pluginCompatibilityInfoKey) { PropertyList.Object.Array(mutableListOf()) }
            .array
        Console.muted(
            "Previous Xcode installation IDs: ${
                oldPluginCompatibilityIds.mapNotNull { it.stringOrNull?.value }.joinToString()
            }"
        )
        oldPluginCompatibilityIds.addAll(additionalPluginCompatibilityIds)
        val distinctPluginCompatibilityIds =
            oldPluginCompatibilityIds.distinctBy { it.stringOrNull?.value }.toMutableList()
        Console.muted(
            "Xcode installation IDs to save: ${
                distinctPluginCompatibilityIds.mapNotNull { it.stringOrNull?.value }.joinToString()
            }"
        )
        rootDictionary[pluginCompatibilityInfoKey] = PropertyList.Object.Array(distinctPluginCompatibilityIds)
        pluginTargetInfoFile.write(infoPlist.toData(PropertyList.Format.XML))
    }

    suspend fun uninstall() {
        Console.info("Deleting Xcode plugin from ${pluginTargetFile.path}")
        pluginTargetFile.delete()
        XcodeHelper.removeKotlinPluginFromDefaults()
    }

    suspend fun fixXcode15(xcodeInstallations: List<XcodeHelper.XcodeInstallation>): Unit = try {
        val cacheDir = Path(Shell.exec("/usr/bin/getconf", "DARWIN_USER_CACHE_DIR").output.orEmpty().trim())
        Console.info("Enabling IDEPerformanceDebugger built-in plugin.")
        XcodeHelper.setIDEPerformanceDebuggerEnabled(true)

        xcodeInstallations
            .filter { it.version.startsWith("15.") }
            .forEach { installation ->
                Console.info("Opening ${installation.name} in background to generate plugin cache")
                val xcodeRunning = CoroutineScope(coroutineContext + Dispatchers.IO).launch {
                    XcodeHelper.openInBackground(installation)
                }

                try {
                    for (i in 1..fixXcode15Timeout) {
                        delay(1.seconds)

                        val pluginCachePath =
                            cacheDir / "com.apple.DeveloperTools" / "${installation.version}-${installation.build}" / "Xcode" / "PlugInCache-Debug.xcplugincache"

                        if (pluginCachePath.exists()) {
                            Console.info("${installation.name} plugin cache file exists, checking if it contains IDEPerformanceDebugger entry yet")
                            val pluginCache = PropertyList.create(pluginCachePath)
                            val containsIDEPerformanceDebuggerInfo = with(XcodeHelper.PlugInCache) {
                                pluginCache.scanRecords.contains { record ->
                                    record.bundlePath.endsWith("IDEPerformanceDebugger.framework")
                                }
                            }

                            if (containsIDEPerformanceDebuggerInfo) {
                                // Xcode updated the cache and should work now, we're done.
                                Console.info("${installation.name} updated the plugin cache and should work now.")
                                break
                            } else {
                                Console.info("${installation.name} plugin cache doesn't contain IDEPerformanceDebugger entry yet.")
                            }
                        } else {
                            Console.info("${installation.name} plugin cache file doesn't exist yet.")
                        }

                        if (i == fixXcode15Timeout) {
                            error("IDEPerformanceDebugger.framework was not found in ${installation.name} plugin cache after waiting $fixXcode15Timeout seconds. Please try again, or report an issue in the xcode-kotlin repository.")
                        }
                    }
                } finally {
                    Console.info("Killing ${installation.name}")
                    xcodeRunning.cancelAndJoin()
                }
            }
    } finally {
        Console.info("Disabling IDEPerformanceDebugger built-in plugin.")
        XcodeHelper.setIDEPerformanceDebuggerEnabled(false)
    }
}
