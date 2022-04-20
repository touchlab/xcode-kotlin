package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.command.Info
import co.touchlab.xcode.cli.command.Install
import co.touchlab.xcode.cli.command.Repair
import co.touchlab.xcode.cli.command.Uninstall
import kotlinx.cli.ArgParser

fun main(args: Array<String>) {
    val parser = ArgParser("xcode-kotlin")
    parser.subcommands(
        Install(),
        Uninstall(),
        Repair(),
        Info(),
    )

    parser.parse(args)
}
