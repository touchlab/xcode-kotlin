package co.touchlab.xcode.cli

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.command.Install
import co.touchlab.xcode.cli.util.Console

object InstallationFacade {
    private val logger = Logger.withTag("InstallationFacade")

    fun installAll(xcodeInstallations: List<XcodeHelper.XcodeInstallation>, fixXcode15: Boolean) {
        XcodeHelper.ensureXcodeNotRunning()

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

            if (!Console.confirm(confirmation)) {
                return
            }

            logger.v { "Installation confirmed." }
            logger.i { notification }
            uninstallAll()
        } else {
            logger.i { "Installing $bundledVersion." }
        }

        PluginManager.install()
        PluginManager.disable(bundledVersion, xcodeInstallations)
        if (fixXcode15) {
            PluginManager.fixXcode15(xcodeInstallations)
        }
        PluginManager.sync(xcodeInstallations)
        LangSpecManager.install()
        LLDBInitManager.install()
        PluginManager.enable(bundledVersion, xcodeInstallations)

        logger.i { "Installation complete." }
    }

    fun enable(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion ?: run {
            Console.echo("Plugin not installed, nothing to enable.")
            return
        }

        PluginManager.enable(installedVersion, xcodeInstallations)

        logger.i { "Plugin enabled." }
    }

    fun disable(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion ?: run {
            Console.echo("Plugin not installed, nothing to disable.")
            return
        }

        PluginManager.disable(installedVersion, xcodeInstallations)

        logger.i { "Plugin disabled." }
    }

    fun fixXcode15(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion
        try {
            if (installedVersion != null) {
                PluginManager.disable(installedVersion, xcodeInstallations)
            }

            PluginManager.fixXcode15(xcodeInstallations)
        } finally {
            if (installedVersion != null) {
                PluginManager.enable(installedVersion, xcodeInstallations)
            }
        }

        logger.i { "Xcode 15 fix applied." }
    }

    fun sync(xcodeInstallations: List<XcodeHelper.XcodeInstallation>, fixXcode15: Boolean) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion ?: run {
            Console.echo("Plugin not installed, nothing to synchronize.")
            return
        }

        PluginManager.disable(installedVersion, xcodeInstallations)
        PluginManager.sync(xcodeInstallations)
        if (fixXcode15) {
            PluginManager.fixXcode15(xcodeInstallations)
        }
        PluginManager.enable(installedVersion, xcodeInstallations)

        logger.i { "Synchronization complete." }
    }

    fun uninstallAll() {
        logger.v { "Will uninstall all plugin components." }
        XcodeHelper.ensureXcodeNotRunning()
        PluginManager.uninstall()
        LangSpecManager.uninstall()
        LLDBInitManager.uninstall()

        logger.i { "Uninstallation complete." }
    }
}
