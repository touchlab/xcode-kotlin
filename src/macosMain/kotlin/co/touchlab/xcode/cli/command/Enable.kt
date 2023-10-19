package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade

class Enable: BaseXcodeListSubcommand("enable", "Enables Xcode Kotlin plugin") {
    override fun execute() {
        InstallationFacade.enable(xcodeInstallations())
    }
}
