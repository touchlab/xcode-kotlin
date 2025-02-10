package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option

class Install: BaseXcodeListSubcommand("install", "Installs Xcode Kotlin plugin") {
    private val noFixXcode15 by option(
        "--no-fix-xcode15",
        help = "Do not apply Xcode 15 workaround.",
    ).flag(default = false)

    override suspend fun run() {
        InstallationFacade.installAll(xcodeInstallations(), !noFixXcode15)
    }
}
