package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.BackupHelper
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.PropertyList
import co.touchlab.xcode.cli.util.SemVer
import co.touchlab.xcode.cli.util.Shell
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import platform.Foundation.NSNumber
import platform.Foundation.numberWithBool
import platform.posix.exit

object XcodeHelper {
    val xcodeLibraryPath = Path.home / "Library" / "Developer" / "Xcode"

    private val xcodeProcessName = "Xcode"
    private val xcodeVersionRegex = Regex("(\\S+) \\((\\S+)\\)")

    suspend fun ensureXcodeNotRunning() {
        Console.muted("Checking if any Xcode runs.")
        val result = Shell.exec("/usr/bin/pgrep", "-xq", "--", xcodeProcessName)
        if (result.success) {
            Console.muted("Found running Xcode instance.")
            val shutdown = Console.confirm("Xcode is running. Attempt to shut down?")
            if (shutdown) {
                Console.muted("Shutting down Xcode.")
                Console.echo("Shutting down Xcode...")
                killRunningXcode().checkSuccessful {
                    "Couldn't shut down Xcode!"
                }
            } else {
                Console.danger("Xcode needs to be closed!")
                exit(1)
            }
        } else {
            Console.muted("No running Xcode found.")
        }
    }

    suspend fun openInBackground(installation: XcodeInstallation) {
        val xcodeBinaryPath = installation.path / "Contents" / "MacOS" / "Xcode"
        Console.info("Opening Xcode binary in background ($xcodeBinaryPath).")
//        Console.echo("Opening realXcodePath in background.")

//        Shell.exec("/usr/bin/open", "-gjF", xcodeBinaryPath.value)
        Shell.exec(xcodeBinaryPath.value).checkSuccessful {
            "Couldn't open ${installation.name} at $xcodeBinaryPath!"
        }
    }

    suspend fun killRunningXcode(): Shell.ExecutionResult {
        return Shell.exec("/usr/bin/pkill", "-x", xcodeProcessName)
    }

    suspend fun allXcodeInstallations(): List<XcodeInstallation> {
        val result = Shell.exec("/usr/sbin/system_profiler", "-json", "SPDeveloperToolsDataType")
            .checkSuccessful { "Couldn't get list of installed developer tools." }

        val json = Json {
            ignoreUnknownKeys = true
        }

        if (result.output == null) {
            error("Missing output from system_profiler!")
        }
        val output = json.decodeFromString(SystemProfilerOutput.serializer(), result.output)
        return output.developerTools
            .map {
                installationAt(Path(it.path))
            }
    }

    suspend fun installationAt(path: Path): XcodeInstallation {
        val xcodeFile = File(path)
        require(xcodeFile.exists()) { "Path $path doesn't exist!" }
        val versionPlist = PropertyList.create(path / "Contents" / "version.plist")
        val version = with(XcodeVersion) {
            checkNotNull(versionPlist.version?.trim()) { "Couldn't get version of Xcode at $path." }
        }
        val build = with(XcodeVersion) {
            checkNotNull(versionPlist.build?.trim()) { "Couldn't get build number of Xcode at $path." }
        }

        if (version15_3_orHigher(version)) {
            return XcodeInstallation(
                version = version,
                build = build,
                path = path
            )
        }

        val xcodeInfoPath = path / "Contents" / "Info"
        val pluginCompatabilityIdResult =
            Shell.exec("/usr/bin/defaults", "read", xcodeInfoPath.value, "DVTPlugInCompatibilityUUID")
                .checkSuccessful {
                    "Couldn't get plugin compatibility UUID from Xcode at ${path}."
                }
        val pluginCompatabilityId = checkNotNull(pluginCompatabilityIdResult.output?.trim()) {
            "Couldn't get plugin compatibility ID of Xcode at path: ${path}."
        }
        return XcodeInstallation(
            version = version,
            build = build,
            path = path,
            pluginCompatabilityId = pluginCompatabilityId,
        )
    }

    suspend fun allowKotlinPlugin(pluginVersion: SemVer, xcodeInstallations: List<XcodeInstallation>) {
        Console.info("Adding plugin to allowed list in Xcode defaults.")
        modifyingXcodeDefaults("BeforeAdd") {
            for (installation in xcodeInstallations) {
                it.nonApplePlugins(installation.version).allowed.add(xcodeKotlinBundleId, pluginVersion.toString())
            }
        }
    }

    suspend fun skipKotlinPlugin(pluginVersion: SemVer, xcodeInstallations: List<XcodeInstallation>) {
        Console.info("Adding plugin to skipped list in Xcode defaults.")
        modifyingXcodeDefaults("BeforeSkip") {
            for (installation in xcodeInstallations) {
                it.nonApplePlugins(installation.version).skipped.add(xcodeKotlinBundleId, pluginVersion.toString())
            }
        }
    }

    suspend fun removeKotlinPluginFromDefaults() {
        Console.info("Removing plugin from allowed/skipped list in Xcode defaults.")
        modifyingXcodeDefaults("BeforeRemove") { properties ->
            properties.allNonApplePlugins().forEach {
                it.allowed.remove(xcodeKotlinBundleId)
                it.skipped.remove(xcodeKotlinBundleId)
            }
        }
    }

    suspend fun setIDEPerformanceDebuggerEnabled(enabled: Boolean) {
        Console.info("Setting IDEPerformanceDebuggerEnabled to $enabled in Xcode defaults.")
        modifyingXcodeDefaults("BeforeIDEPerformanceDebuggerEnabled-$enabled") {
            it.root.dictionary["IDEPerformanceDebuggerEnabled"] = PropertyList.Object.Number(
                NSNumber.numberWithBool(enabled)
            )
        }
    }

    private suspend inline fun modifyingXcodeDefaults(backupTag: String, modify: Defaults.(PropertyList) -> Unit) {
        val backupPath = BackupHelper.backupPath("XcodeDefaults_$backupTag.plist")
        Console.info("Saving a backup of com.apple.dt.Xcode defaults to `$backupPath`")
        Shell.exec("/usr/bin/defaults", "export", "com.apple.dt.Xcode", backupPath.value).checkSuccessful {
            "Couldn't export Xcode defaults."
        }
        val defaultsPlist = PropertyList.create(backupPath)
        Defaults.modify(defaultsPlist)
        val newPlistData = defaultsPlist.toData(PropertyList.Format.XML)
        Shell.exec("/usr/bin/defaults", "import", "com.apple.dt.Xcode", "-", input = newPlistData).checkSuccessful {
            "Couldn't import new Xcode defaults."
        }
    }

    data class XcodeInstallation(
        val version: String,
        val build: String,
        val path: Path,
        val pluginCompatabilityId: String? = null,
    ) {
        val name: String = "Xcode $version ($build)"

        fun supported(supportedXcodeUuids: Set<String>): Boolean = version15_3_orHigher(version) ||
                supportedXcodeUuids.contains(pluginCompatabilityId)
    }

    fun version15_3_orHigher(version: String) = SemVer.parse(version) >= SemVer.parse("15.3")

    @Serializable
    private data class SystemProfilerOutput(
        @SerialName("SPDeveloperToolsDataType")
        val developerTools: List<DeveloperTool>
    ) {
        @Serializable
        data class DeveloperTool(
            @SerialName("spdevtools_path")
            val path: String,
            @SerialName("spdevtools_version")
            val version: String,
        )
    }

    private object XcodeVersion {
        val PropertyList.version: String?
            get() = root.dictionary["CFBundleShortVersionString"]?.stringOrNull?.value

        val PropertyList.build: String?
            get() = root.dictionary["ProductBuildVersion"]?.stringOrNull?.value
    }

    object PlugInCache {
        val PropertyList.scanRecords: DVTScanRecords
            get() = DVTScanRecords(root.dictionary["DVTScanRecords"]?.arrayOrNull ?: PropertyList.Object.Array())

        class DVTScanRecords(private val backingArray: PropertyList.Object.Array) {
            fun contains(block: (Record) -> Boolean): Boolean {
                return backingArray.any { block(Record(it.dictionary)) }
            }

            class Record(private val backingDictionary: PropertyList.Object.Dictionary) {
                val bundlePath: String
                    get() = backingDictionary["bundlePath"]?.stringOrNull?.value ?: ""
            }
        }
    }

    private object Defaults {
        val xcodeKotlinBundleId = "org.kotlinlang.xcode.kotlin"
        private val nonApplePluginsKeyPrefix = "DVTPlugInManagerNonApplePlugIns-Xcode-"

        fun PropertyList.allNonApplePlugins(): List<NonApplePlugins> {
            return root.dictionary.filter { (key, _) -> key.startsWith(nonApplePluginsKeyPrefix) }.map { (_, value) ->
                NonApplePlugins(value.dictionary)
            }
        }

        fun PropertyList.nonApplePlugins(xcodeVersion: String): NonApplePlugins {
            val backingDictionary = root.dictionary.getOrPut(nonApplePluginsKeyPrefix + xcodeVersion) {
                PropertyList.Object.Dictionary(
                    mutableMapOf(
                        "allowed" to PropertyList.Object.Dictionary(),
                        "skipped" to PropertyList.Object.Dictionary(),
                    )
                )
            }.dictionary
            return NonApplePlugins(backingDictionary)
        }

        class NonApplePlugins(private val backingDictionary: PropertyList.Object.Dictionary) {
            val allowed: PluginEntries
                get() = entries("allowed")
            val skipped: PluginEntries
                get() = entries("skipped")

            private fun entries(key: String): PluginEntries {
                return PluginEntries(
                    backingDictionary.getOrPut(key) { PropertyList.Object.Dictionary() }.dictionary
                )
            }

            class PluginEntries(private val backingDictionary: PropertyList.Object.Dictionary) {
                fun add(bundleId: String, version: String) {
                    backingDictionary[bundleId] = PropertyList.Object.Dictionary(
                        mutableMapOf(
                            "version" to PropertyList.Object.String(version)
                        )
                    )
                }

                fun remove(bundleId: String) {
                    backingDictionary.remove(bundleId)
                }
            }
        }
    }
}
