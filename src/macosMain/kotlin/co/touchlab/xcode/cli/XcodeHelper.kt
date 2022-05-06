package co.touchlab.xcode.cli

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.util.BackupHelper
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.PropertyList
import co.touchlab.xcode.cli.util.Shell
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import platform.posix.exit

object XcodeHelper {
    val xcodeLibraryPath = Path.home / "Library" / "Developer" / "Xcode"

    private val logger = Logger.withTag("XcodeHelper")
    private val xcodeProcessName = "Xcode"
    private val xcodeVersionRegex = Regex("(\\S+) \\((\\S+)\\)")

    fun ensureXcodeNotRunning() {
        logger.v { "Checking if any Xcode runs." }
        val result = Shell.exec("/usr/bin/pgrep", "-xq", "--", xcodeProcessName)
        if (result.success) {
            logger.v { "Found running Xcode instance." }
            val shutdown = Console.confirm("Xcode is running. Attempt to shut down? y/n: ")
            if (shutdown) {
                logger.v { "Shutting down Xcode." }
                Console.echo("Shutting down Xcode...")
                Shell.exec("/usr/bin/pkill", "-x", xcodeProcessName).checkSuccessful {
                    "Couldn't shut down Xcode!"
                }
            } else {
                Console.printError("Xcode needs to be closed!")
                exit(1)
            }
        } else {
            logger.v { "No running Xcode found." }
        }
    }

    fun allXcodeInstallations(): List<XcodeInstallation> {
        val result = Shell.exec("/usr/sbin/system_profiler", "-json", "SPDeveloperToolsDataType").checkSuccessful {
            "Couldn't get list of installed developer tools."
        }

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

    fun installationAt(path: Path): XcodeInstallation {
        val xcodeFile = File(path)
        require(xcodeFile.exists()) { "Path $path doesn't exist!" }
        val xcodeInfoPath = path / "Contents" / "Info"
        val versionResult = Shell.exec("/usr/bin/defaults", "read", xcodeInfoPath.value, "CFBundleShortVersionString")
            .checkSuccessful {
                "Couldn't get version of Xcode at $path."
            }
        val buildResult = Shell.exec("/usr/bin/defaults", "read", xcodeInfoPath.value, "DTXcodeBuild")
            .checkSuccessful {
                "Couldn't get build number of Xcode at $path."
            }
        val pluginCompatabilityIdResult = Shell.exec("/usr/bin/defaults", "read", xcodeInfoPath.value, "DVTPlugInCompatibilityUUID")
            .checkSuccessful {
                "Couldn't get plugin compatibility UUID from Xcode at ${path}."
            }
        val version = checkNotNull(versionResult.output?.trim()) {
            "Couldn't get version of Xcode at path: ${path}."
        }
        val build = checkNotNull(buildResult.output?.trim()) {
            "Couldn't get version of Xcode at path: ${path}."
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

    fun addKotlinPluginToDefaults(pluginVersion: KotlinVersion, xcodeInstallations: List<XcodeInstallation>) {
        logger.i { "Adding plugin to allowed list in Xcode defaults." }
        modifyingXcodeDefaults("BeforeAdd") {
            for (installation in xcodeInstallations) {
                it.nonApplePlugins(installation.version).allowed.add(xcodeKotlinBundleId, pluginVersion.toString())
            }
        }
    }

    fun removeKotlinPluginFromDefaults() {
        logger.i { "Removing plugin from allowed/skipped list in Xcode defaults." }
        modifyingXcodeDefaults("BeforeRemove") {
            it.allNonApplePlugins().forEach {
                it.allowed.remove(xcodeKotlinBundleId)
                it.skipped.remove(xcodeKotlinBundleId)
            }
        }
    }

    private inline fun modifyingXcodeDefaults(backupTag: String, modify: Defaults.(PropertyList) -> Unit) {
        val backupPath = BackupHelper.backupPath("XcodeDefaults_$backupTag.plist")
        logger.i { "Saving a backup of com.apple.dt.Xcode defaults to `$backupPath`" }
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
        val pluginCompatabilityId: String,
    ) {
        val name: String = "Xcode $version ($build)"
    }

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