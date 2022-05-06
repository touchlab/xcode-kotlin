package co.touchlab.xcode.cli.command

import co.touchlab.xcode.cli.XcodeHelper
import co.touchlab.xcode.cli.util.Path
import kotlinx.cli.ArgType
import kotlinx.cli.Subcommand
import kotlinx.cli.default
import kotlinx.cli.optional
import kotlinx.cli.vararg

abstract class BaseXcodeListSubcommand(name: String, actionDescription: String): Subcommand(name, actionDescription) {
    protected val onlyProvidedXcodeInstallations by option(
        type = ArgType.Boolean,
        fullName = "only",
        description = "Do not auto-discover Xcode installations, use only those provided."
    ).default(false)
    protected val providedXcodePaths by argument(type = ArgType.String, description = "").vararg().optional()

    protected fun xcodeInstallations(): List<XcodeHelper.XcodeInstallation> {
        val providedXcodeInstallations = providedXcodePaths.map { XcodeHelper.installationAt(Path(it)) }
        return if (onlyProvidedXcodeInstallations) {
            providedXcodeInstallations
        } else {
            XcodeHelper.allXcodeInstallations() + providedXcodeInstallations
        }
    }
}