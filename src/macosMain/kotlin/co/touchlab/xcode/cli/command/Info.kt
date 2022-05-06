package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.LLDBInitManager
import co.touchlab.xcode.cli.LangSpecManager
import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.util.Console

class Info: BaseXcodeListSubcommand("info", "Shows information about the plugin") {

    override fun execute() = with(Console) {
        val installedVersion = PluginManager.installedVersion
        val bundledVersion = PluginManager.bundledVersion

        if (installedVersion != null && bundledVersion > installedVersion) {
            echo("Update available! Run 'xcode-kotlin install' to update.")
            echo()
        } else if (installedVersion == null) {
            echo("Plugin not installed. Run 'xcode-kotlin install' to install it.")
            echo()
        }

        val lldbInstalled = LLDBInitManager.isInstalled
        val legacyLldbInstalled = LLDBInitManager.Legacy.isInstalled
        val lldbInstalledString = if (lldbInstalled) {
            "Yes"
        } else if (legacyLldbInstalled) {
            "Legacy"
        } else {
            "No"
        }

        echo("Installed plugin version:\t${installedVersion ?: "none"}")
        echo("Bundled plugin version:\t\t${bundledVersion}")
        echo()
        echo("Language spec installed: ${LangSpecManager.isInstalled.humanReadable}")
        echo("LLDB init installed: $lldbInstalledString")
        echo("LLDB Xcode init sources main LLDB init: ${LLDBInitManager.sourcesMainLlvmInit.humanReadable}")

        val xcodeInstallations = xcodeInstallations()
        if (xcodeInstallations.isNotEmpty()) {
            val supportedXcodeUuids = PluginManager.targetSupportedXcodeUUIds.toSet()
            echo()
            echo("Installed Xcode versions:")
            val longestNameLength = xcodeInstallations.maxOf { it.name.length }
            for (install in xcodeInstallations) {
                val spacesAfterName = (1..(longestNameLength - install.name.length)).joinToString(separator = "") { " " }
                val compatibilityMark = if (supportedXcodeUuids.contains(install.pluginCompatabilityId)) "✔" else "x"
                echo("$compatibilityMark\t${install.name}$spacesAfterName\t${install.pluginCompatabilityId}\t${install.path}")
            }

            echo()
            echo("✔ - plugin is compatible, x - plugin is not compatible")
            echo("Run 'xcode-kotlin sync' to add compatibility for all listed Xcode versions.")
        }
    }

    private val Boolean.humanReadable: String
        get() = if (this) "Yes" else "No"
}