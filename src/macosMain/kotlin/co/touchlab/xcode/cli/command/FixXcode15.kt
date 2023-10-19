package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade

class FixXcode15: BaseXcodeListSubcommand(
    name = "fix-xcode15",
    actionDescription = "Temporarily workarounds Xcode 15 crash that happens when using any non-Apple Xcode plugins.",
) {
    override fun execute() {
        InstallationFacade.fixXcode15(xcodeInstallations())
    }
}
