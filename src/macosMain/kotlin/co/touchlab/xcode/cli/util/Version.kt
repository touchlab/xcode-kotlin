package co.touchlab.xcode.cli.util

typealias Version = KotlinVersion

private val versionRegex = Regex("(\\d+)(?:\\.(\\d+)(?:\\.(\\d+))?)?")
fun KotlinVersion.Companion.fromString(version: String): KotlinVersion {
    val result = requireNotNull(versionRegex.matchEntire(version)) { "Version $version can't be parsed!" }
    val major = result.groupValues[1].toInt()
    val minor = result.groups[2]?.value?.toInt() ?: 0
    val patch = result.groups[3]?.value?.toInt() ?: 0

    // TODO: We might not want to use `KotlinVersion`, but I didn't want to implement our own semver.
    return KotlinVersion(major, minor, patch)
}