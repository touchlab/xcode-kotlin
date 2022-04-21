package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.Path

object Installer {
    fun installAll(xcodes: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        PluginManager.install(xcodes)
        LangSpecManager.install()
        LLDBInitManager.install()
    }
}

