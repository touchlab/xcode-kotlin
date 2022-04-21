package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.LLDBInitManager
import co.touchlab.xcode.cli.LangSpecManager
import co.touchlab.xcode.cli.PluginManager
import co.touchlab.xcode.cli.Uninstaller
import kotlinx.cli.Subcommand

class Uninstall: Subcommand("uninstall", "Uninstalls Xcode Kotlin plugin") {
    override fun execute() {
        Uninstaller.uninstallAll()
    }
}