package co.touchlab.xcode.cli.command

import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.terminal
import com.github.ajalt.mordant.terminal.muted

class XcodeKotlinPlugin(
    private val args: Array<String>,
): SuspendingCliktCommand() {
    override suspend fun run() {
        terminal.muted("Running xcode-cli with arguments: ${args.joinToString()}")
    }
}
