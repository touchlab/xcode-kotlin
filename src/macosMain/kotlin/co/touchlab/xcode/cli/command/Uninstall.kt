package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.InstallationFacade
import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.Context

class Uninstall: SuspendingCliktCommand("uninstall") {
    override fun help(context: Context): String {
        return "Uninstalls Xcode Kotlin plugin"
    }

    override suspend fun run() {
        InstallationFacade.uninstallAll()
    }
}
