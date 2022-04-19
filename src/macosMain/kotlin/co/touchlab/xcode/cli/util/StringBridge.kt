package co.touchlab.xcode.cli.util

import platform.Foundation.NSString

val String.objc: NSString
    // String can be casted to NSString, for some reason the Kotlin compiler doesn't know.
    @Suppress("CAST_NEVER_SUCCEEDS")
    get() = this as NSString

val NSString.kt: String
    // NSString can be casted back to NSString, for some reason the Kotlin compiler doesn't know.
    @Suppress("CAST_NEVER_SUCCEEDS")
    get() = this as String