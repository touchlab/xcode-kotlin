package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade
import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.XcodeHelper
import kotlinx.cli.ArgType
import kotlinx.cli.default

class Sync: BaseXcodeListSubcommand("sync", "Adds IDs of Xcode installations to the currently installed Xcode Kotlin plugin") {
    private val noFixXcode15 by option(
        type = ArgType.Boolean,
        fullName = "no-fix-xcode15",
        description = "Do not apply Xcode 15 workaround."
    ).default(false)

    override fun execute() {
        InstallationFacade.sync(xcodeInstallations(), !noFixXcode15)
    }
}
