package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.command.Disable
import co.touchlab.xcode.cli.command.Enable
import co.touchlab.xcode.cli.command.FixXcode15
import co.touchlab.xcode.cli.command.Info
import co.touchlab.xcode.cli.command.Install
import co.touchlab.xcode.cli.command.Sync
import co.touchlab.xcode.cli.command.Uninstall
import co.touchlab.xcode.cli.command.XcodeKotlinPlugin
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.CrashHelper
import com.github.ajalt.clikt.command.main
import com.github.ajalt.clikt.core.context
import com.github.ajalt.clikt.core.subcommands
import com.github.ajalt.clikt.core.terminal
import kotlinx.coroutines.runBlocking
import platform.posix.exit

fun main(args: Array<String>) {
    val crashHelper = CrashHelper()

    try {
        val command = XcodeKotlinPlugin(args)
            .context {
                this.terminal = Console.terminal
            }
            .subcommands(
                Install(),
                Uninstall(),
                Sync(),
                Info(),
                FixXcode15(),
                Enable(),
                Disable(),
            )

        runBlocking {
            command.main(args)
        }
    } catch (e: Throwable) {
        if (Console.confirm("xcode-kotlin has crashed, do you want to upload the crash report to Touchlab?")) {
            Console.echo("Uploading crash report.")
            try {
                crashHelper.upload(e, Console.terminalRecorder.recorder)
                Console.success("Upload successful")
                exit(1)
            } catch (uploadException: Throwable) {
                Console.danger("Uploading crash report failed!")
                e.addSuppressed(uploadException)
                throw e
            }
        } else {
            throw e
        }
    }
}
