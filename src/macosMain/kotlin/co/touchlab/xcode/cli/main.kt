package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.command.Info
import kotlinx.cli.ArgParser

fun main(args: Array<String>) {
    val parser = ArgParser("xcode-kotlin")
    parser.subcommands(
        Info(),
    )

    parser.parse(args)
}