package co.touchlab.xcode.cli

import platform.Foundation.NSFileManager

object LangSpecManager {
    val specName = "Kotlin.xclangspec"
    val specTargetUrl = XcodeHelper.xcodeLibraryPath / "Specifications" / specName

    val isInstalled: Boolean
        get() = NSFileManager.defaultManager.fileExistsAtPath(specTargetUrl.value)

}