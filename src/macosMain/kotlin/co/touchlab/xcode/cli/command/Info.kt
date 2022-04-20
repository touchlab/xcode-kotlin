package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.XcodeHelper
import kotlinx.cli.Subcommand

class Info: Subcommand("info", "Shows information about the plugin") {
    override fun execute() = with(Console) {
        echo("Installed plugin version:\t${PluginManager.installedVersion ?: "none"}")
        echo("Bundled plugin version:\t\t${PluginManager.bundledVersion}")
        val installedXcodes = XcodeHelper.installedXcodes()
        if (installedXcodes.isNotEmpty()) {
            echo("")
            echo("Installed Xcodes:")
            val longestNameLength = installedXcodes.maxOf { it.name.length }
            for (install in installedXcodes) {
                val spacesAfterName = (1..(longestNameLength - install.name.length)).joinToString(separator = "") { " " }
                echo("\t${install.name}$spacesAfterName\t${XcodeHelper.pluginCompatibilityUuid(install)}\t${install.path}")
            }
        }
    }
}