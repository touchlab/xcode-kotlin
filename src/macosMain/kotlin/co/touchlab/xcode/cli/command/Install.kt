package co.touchlab.xcode.cli.command

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.Installer
import co.touchlab.xcode.cli.LLDBInitManager
import co.touchlab.xcode.cli.LangSpecManager
import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.Uninstaller
import co.touchlab.xcode.cli.XcodeHelper
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.Path
import kotlinx.cli.ArgType
import kotlinx.cli.Subcommand
import kotlinx.cli.default
import kotlinx.cli.optional
import kotlinx.cli.vararg
import kotlin.test.fail

class Install: BaseXcodeListSubcommand("install", "Installs Xcode Kotlin plugin") {
    override fun execute() = with(Console) {
        logger.v { "Running 'install' subcommand." }

        val bundledVersion = PluginManager.bundledVersion
        logger.v { "Bundled plugin version = $bundledVersion" }
        val installedVersion = PluginManager.installedVersion
        logger.v { "Installed plugin version = ${installedVersion ?: "N/A"}" }

        if (installedVersion != null) {
            val (confirmation, notification) = when {
                bundledVersion > installedVersion -> {
                    "Do you want to update from $installedVersion to $bundledVersion? y/n: " to "Updating to $bundledVersion"
                }
                bundledVersion == installedVersion -> {
                    "Do you want to reinstall version $installedVersion? y/n: " to "Reinstalling $installedVersion"
                }
                bundledVersion < installedVersion -> {
                    "Do you want to downgrade from $installedVersion to $bundledVersion? y/n: " to "Downgrading to $bundledVersion"
                }
                else -> error("Unhandled comparison possibility!")
            }

            if (confirm(confirmation)) {
                logger.v { "Installation confirmed." }
                echo(notification)
                uninstall()
                install()
            }
        } else {
            echo("Installing $bundledVersion.")
            install()
        }
    }

    private fun install() {
        Installer.installAll(xcodeInstallations())
    }

    private fun uninstall() {
        Uninstaller.uninstallAll()
    }

    private companion object {
        val logger = Logger.withTag("Install")
    }
}