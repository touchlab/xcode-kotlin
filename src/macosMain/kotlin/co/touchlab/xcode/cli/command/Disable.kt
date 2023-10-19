package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade

class Disable: BaseXcodeListSubcommand("disable", "Disables Xcode Kotlin plugin without uninstalling") {
    override fun execute() {
        InstallationFacade.disable(xcodeInstallations())
    }
}
