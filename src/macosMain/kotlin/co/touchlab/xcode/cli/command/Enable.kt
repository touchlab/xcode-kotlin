package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade

class Enable: BaseXcodeListSubcommand("enable", "Enables Xcode Kotlin plugin") {
    override suspend fun run() {
        InstallationFacade.enable(xcodeInstallations())
    }
}
