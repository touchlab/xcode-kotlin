package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade
import kotlinx.cli.Subcommand

class Uninstall: Subcommand("uninstall", "Uninstalls Xcode Kotlin plugin") {
    override fun execute() {
        InstallationFacade.uninstallAll()
    }
}
