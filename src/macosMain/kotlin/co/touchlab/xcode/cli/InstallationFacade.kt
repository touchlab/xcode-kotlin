package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.Console

object InstallationFacade {
    suspend fun installAll(xcodeInstallations: List<XcodeHelper.XcodeInstallation>, fixXcode15: Boolean) {
        XcodeHelper.ensureXcodeNotRunning()

        val bundledVersion = PluginManager.bundledVersion
        Console.muted("Bundled plugin version = $bundledVersion")
        val installedVersion = PluginManager.installedVersion
        Console.muted("Installed plugin version = ${installedVersion ?: "N/A"}")

        if (installedVersion != null) {
            val (confirmation, notification) = when {
                bundledVersion > installedVersion -> {
                    "Do you want to update from $installedVersion to $bundledVersion?" to "Updating to $bundledVersion"
                }
                bundledVersion == installedVersion -> {
                    "Do you want to reinstall version $installedVersion?" to "Reinstalling $installedVersion"
                }
                bundledVersion < installedVersion -> {
                    "Do you want to downgrade from $installedVersion to $bundledVersion?" to "Downgrading to $bundledVersion"
                }
                else -> error("Unhandled comparison possibility!")
            }

            if (!Console.confirm(confirmation)) {
                return
            }

            Console.muted("Installation confirmed.")
            Console.info(notification)
            uninstallAll()
        } else {
            Console.info("Installing $bundledVersion.")
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

        Console.info("Installation complete.")
    }

    suspend fun enable(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion ?: run {
            Console.warning("Plugin not installed, nothing to enable.")
            return
        }

        PluginManager.enable(installedVersion, xcodeInstallations)

        Console.info("Plugin enabled.")
    }

    suspend fun disable(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion ?: run {
            Console.warning("Plugin not installed, nothing to disable.")
            return
        }

        PluginManager.disable(installedVersion, xcodeInstallations)

        Console.info("Plugin disabled.")
    }

    suspend fun fixXcode15(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
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

        Console.info("Xcode 15 fix applied.")
    }

    suspend fun sync(xcodeInstallations: List<XcodeHelper.XcodeInstallation>, fixXcode15: Boolean) {
        XcodeHelper.ensureXcodeNotRunning()

        val installedVersion = PluginManager.installedVersion ?: run {
            Console.warning("Plugin not installed, nothing to synchronize.")
            return
        }

        PluginManager.disable(installedVersion, xcodeInstallations)
        PluginManager.sync(xcodeInstallations)
        if (fixXcode15) {
            PluginManager.fixXcode15(xcodeInstallations)
        }
        PluginManager.enable(installedVersion, xcodeInstallations)

        Console.info("Synchronization complete.")
    }

    suspend fun uninstallAll() {
        Console.muted("Will uninstall all plugin components.")
        XcodeHelper.ensureXcodeNotRunning()
        PluginManager.uninstall()
        LangSpecManager.uninstall()
        LLDBInitManager.uninstall()

        Console.info("Uninstallation complete.")
    }
}
