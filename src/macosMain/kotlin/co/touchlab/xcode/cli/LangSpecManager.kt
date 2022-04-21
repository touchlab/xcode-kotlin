package co.touchlab.xcode.cli

import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path

object LangSpecManager {
    private val specName = "Kotlin.xclangspec"
    private val specSourceFile = File(Path.dataDir / specName)
    private val specTargetFile = File(XcodeHelper.xcodeLibraryPath / "Specifications" / specName)

    val isInstalled: Boolean
        get() = specTargetFile.exists()

    fun install() {
        check(!specTargetFile.exists()) { "Language spec file exists at path ${specTargetFile.path}! Delete it first." }
        specSourceFile.copy(specTargetFile.path)
    }

    fun uninstall() {
        specTargetFile.delete()
    }
}