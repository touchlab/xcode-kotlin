package co.touchlab.xcode.cli

object Uninstaller {
    fun uninstallAll() {
        XcodeHelper.ensureXcodeNotRunning()
        PluginManager.uninstall()
        LangSpecManager.uninstall()
        LLDBInitManager.uninstall()
    }
}