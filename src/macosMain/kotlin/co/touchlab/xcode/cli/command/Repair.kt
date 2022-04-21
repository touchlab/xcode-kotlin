package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.XcodeHelper
import co.touchlab.xcode.cli.util.Path

class Repair: BaseXcodeListSubcommand("repair", "Repairs currently installed Xcode Kotlin plugin") {
    override fun execute() {
        XcodeHelper.ensureXcodeNotRunning()
        PluginManager.repair(xcodeInstallations())
    }
}

