package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path

object LangSpecManager {
    private val specName = "Kotlin.xclangspec"
    private val specSourceFile = File(Path.dataDir / specName)
    private val specsDirectory = File(XcodeHelper.xcodeLibraryPath / "Specifications")
    private val specTargetFile = File(specsDirectory.path / specName)

    val isInstalled: Boolean
        get() = specTargetFile.exists()

    fun install() {
        check(!specTargetFile.exists()) { "Language spec file exists at path ${specTargetFile.path}! Delete it first." }
        Console.muted("Ensuring language specification directory exists at ${specsDirectory.path}")
        specsDirectory.mkdirs()
        Console.muted("Copying language specification to target path ${specTargetFile.path}")
        specSourceFile.copy(specTargetFile.path)
    }

    fun uninstall() {
        Console.muted("Deleting language specification from ${specTargetFile.path}.")
        specTargetFile.delete()
    }
}
