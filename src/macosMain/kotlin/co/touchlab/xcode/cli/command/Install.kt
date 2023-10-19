package co.touchlab.xcode.cli.command

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.InstallationFacade
import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.util.Console
import kotlinx.cli.ArgType
import kotlinx.cli.default

class Install: BaseXcodeListSubcommand("install", "Installs Xcode Kotlin plugin") {
    private val noFixXcode15 by option(
        type = ArgType.Boolean,
        fullName = "no-fix-xcode15",
        description = "Do not apply Xcode 15 workaround."
    ).default(false)

    override fun execute() {
        InstallationFacade.installAll(xcodeInstallations(), !noFixXcode15)
    }
}
