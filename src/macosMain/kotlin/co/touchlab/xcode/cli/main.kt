package co.touchlab.xcode.cli

import co.touchlab.kermit.CommonWriter
import co.touchlab.kermit.Logger
import co.touchlab.kermit.platformLogWriter
import co.touchlab.xcode.cli.command.Info
import co.touchlab.xcode.cli.command.Install
import co.touchlab.xcode.cli.command.Repair
import co.touchlab.xcode.cli.command.Uninstall
import co.touchlab.xcode.cli.util.CrashHelper
import kotlinx.cli.ArgParser

fun main(args: Array<String>) {
    val crashHelper = CrashHelper()
    crashHelper.uploadPreviousCrashIfNeeded()

    try {
        val logWriters = if (args.contains("--log-console")) {
            listOf(platformLogWriter(), CommonWriter(), crashHelper)
        } else {
            listOf(platformLogWriter(), crashHelper)
        }

        Logger.setLogWriters(logWriters)
        Logger.v { "Running xcode-cli with arguments: ${args.joinToString()}" }

        // If no arguments were given, we want to show help.
        val adjustedArgs = if (args.isEmpty()) {
            arrayOf("-h")
        } else {
            args.filter { it != "--log-console" }.toTypedArray()
        }
        val parser = ArgParser("xcode-kotlin")
        parser.subcommands(
            Install(),
            Uninstall(),
            Repair(),
            Info(),
        )

        parser.parse(adjustedArgs)
    } catch (e: Throwable) {
        Logger.e("Capturing global exception")
        crashHelper.capture(e)
        crashHelper.upload()
    }
}
