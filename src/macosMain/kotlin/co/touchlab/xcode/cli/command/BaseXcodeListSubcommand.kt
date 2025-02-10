package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.XcodeHelper
import co.touchlab.xcode.cli.util.Path
import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.arguments.argument
import com.github.ajalt.clikt.parameters.arguments.multiple
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option


abstract class BaseXcodeListSubcommand(
    name: String,
    private val actionDescription: String,
): SuspendingCliktCommand(name) {
    protected val onlyProvidedXcodeInstallations by option(
        "--only",
        help = "Do not auto-discover Xcode installations, use only those provided.",
    ).flag(default = false, defaultForHelp = "disabled")
    protected val providedXcodePaths by argument().multiple()

    override fun help(context: Context): String {
        return actionDescription
    }

    protected suspend fun xcodeInstallations(): List<XcodeHelper.XcodeInstallation> {
        val providedXcodeInstallations = providedXcodePaths.map { XcodeHelper.installationAt(Path(it)) }
        return if (onlyProvidedXcodeInstallations) {
            providedXcodeInstallations
        } else {
            XcodeHelper.allXcodeInstallations() + providedXcodeInstallations
        }
    }
}
