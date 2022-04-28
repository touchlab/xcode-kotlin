package co.touchlab.xcode.cli

object Installer {
    fun installAll(xcodeInstallations: List<XcodeHelper.XcodeInstallation>) {
        XcodeHelper.ensureXcodeNotRunning()

        PluginManager.install(xcodeInstallations)
        LangSpecManager.install()
        LLDBInitManager.install()
    }
}

