package co.touchlab.xcode.cli

import co.touchlab.kermit.Logger

object Uninstaller {
    private val logger = Logger.withTag("Uninstaller")
    fun uninstallAll() {
        logger.v { "Will uninstall all plugin components." }
        XcodeHelper.ensureXcodeNotRunning()
        PluginManager.uninstall()
        LangSpecManager.uninstall()
        LLDBInitManager.uninstall()
    }
}