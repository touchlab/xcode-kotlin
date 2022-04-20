package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.PropertyList
import co.touchlab.xcode.cli.util.Shell
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import platform.Foundation.NSHomeDirectory
import platform.posix.exit

object XcodeHelper {
    val xcodeLibraryPath = Path(NSHomeDirectory()) / "Library" / "Developer" / "Xcode"

    private val xcodeProcessName = "Xcode"
    private val xcodeVersionRegex = Regex("(\\S+) \\((\\S+)\\)")

    fun ensureXcodeNotRunning() {
        val result = Shell.exec("/usr/bin/pgrep", "-xq", "--", xcodeProcessName)
        if (result.success) {
            val shutdown = Console.confirm("Xcode is running. Attempt to shut down? y/n: ")
            if (shutdown) {
                Console.echo("Shutting down Xcode...")
                if (!Shell.exec("/usr/bin/pkill", "-x", xcodeProcessName).success) {
                    Console.printError("Couldn't shut down Xcode!")
                    exit(1)
                }
            } else {
                Console.printError("Xcode needs to be closed!")
                exit(1)
            }
        }
    }

    fun installedXcodes(): List<XcodeInstallation> {
        val result = Shell.exec("/usr/sbin/system_profiler", "-json", "SPDeveloperToolsDataType")

        val json = Json {
            ignoreUnknownKeys = true
        }

        if (result.output == null) {
            TODO("Log error!")
        }
        val output = json.decodeFromString(SystemProfilerOutput.serializer(), result.output)
        return output.developerTools
            .map {
                val matchResult = checkNotNull(xcodeVersionRegex.matchEntire(it.version)) {
                    "Couldn't determine Xcode version from ${it.version}"
                }
                XcodeInstallation(
                    version = matchResult.groupValues[1],
                    build = matchResult.groupValues[2],
                    path = Path(it.path),
                )
            }
    }

    fun pluginCompatibilityUuid(installation: XcodeInstallation): String {
        val result = Shell.exec("/usr/bin/defaults", "read", (installation.path / "Contents" / "Info").value, "DVTPlugInCompatibilityUUID")
        return checkNotNull(result.output?.trim()) {
            "Plugin compatibility ID was null! Install path: ${installation.path}."
        }
    }

    data class XcodeInstallation(
        val version: String,
        val build: String,
        val path: Path,
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
}