package co.touchlab.xcode.cli

import co.touchlab.kermit.CommonWriter
import co.touchlab.kermit.Logger
import co.touchlab.kermit.platformLogWriter
import co.touchlab.xcode.cli.command.*
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.CrashHelper
import kotlinx.cli.ArgParser
import platform.posix.exit

fun main(args: Array<String>) {
    val crashHelper = CrashHelper()

    try {
        val logWriters = if (args.contains("--log-console")) {
            listOf(platformLogWriter(), CommonWriter(), crashHelper)
        } else {
            listOf(platformLogWriter(), EchoWriter(), crashHelper)
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
            Sync(),
            Info(),
            FixXcode15(),
            Enable(),
            Disable(),
        )

        parser.parse(adjustedArgs)
    } catch (e: Throwable) {
        if (Console.confirm("xcode-kotlin has crashed, do you want to upload the crash report to Touchlab? y/n: ")) {
            Console.echo("Uploading crash report.")
            try {
                crashHelper.upload(e)
                Console.echo("Upload successful")
                exit(1)
            } catch (uploadException: Throwable) {
                Console.printError("Uploading crash report failed!")
                e.addSuppressed(uploadException)
                throw e
            }
        } else {
            throw e
        }
    }
}
