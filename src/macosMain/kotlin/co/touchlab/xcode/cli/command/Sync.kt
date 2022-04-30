package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.XcodeHelper

class Sync: BaseXcodeListSubcommand("sync", "Adds IDs of Xcode installations to the currently installed Xcode Kotlin plugin") {
    override fun execute() {
        XcodeHelper.ensureXcodeNotRunning()
        PluginManager.sync(xcodeInstallations())
    }
}

