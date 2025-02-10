package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option

class Sync: BaseXcodeListSubcommand("sync", "Adds IDs of Xcode installations to the currently installed Xcode Kotlin plugin") {
    private val noFixXcode15 by option(
        "--no-fix-xcode15",
        help = "Do not apply Xcode 15 workaround."
    ).flag()

    override suspend fun run() {
        InstallationFacade.sync(xcodeInstallations(), !noFixXcode15)
    }
}
