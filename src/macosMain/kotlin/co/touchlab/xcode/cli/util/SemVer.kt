/*
    MIT License

    Copyright (c) 2017 Eric Li

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
 */
package co.touchlab.xcode.cli.util

import kotlin.math.min

/**
 * Version number in [Semantic Versioning 2.0.0](http://semver.org/spec/v2.0.0.html) specification (SemVer).
 *
 * @property major major version, increment it when you make incompatible API changes.
 * @property minor minor version, increment it when you add functionality in a backwards-compatible manner.
 * @property patch patch version, increment it when you make backwards-compatible bug fixes.
 * @property preRelease pre-release version.
 * @property buildMetadata build metadata.
 */
public data class SemVer(
    val major: Int,
    val minor: Int = 0,
    val patch: Int = 0,
    val preRelease: String? = null,
    val buildMetadata: String? = null,
) : Comparable<SemVer> {

    init {
        require(major >= 0) { "Major version must be a positive number" }
        require(minor >= 0) { "Minor version must be a positive number" }
        require(patch >= 0) { "Patch version must be a positive number" }
        if (preRelease != null) require(PreReleasePattern matches preRelease) { "Pre-release version is not valid" }
        if (buildMetadata != null) require(BuildMetadataPattern matches buildMetadata) { "Build metadata is not valid" }
    }

    /**
     * Create a new [SemVer] with the next major number. Minor and patch number becomes 0.
     * Pre-release and build metadata information is not applied to the new version.
     *
     * @return next major version
     * @throws NumberFormatException if the next major number exceed [Int] range.
     */
    public fun nextMajor(): SemVer {
        return SemVer(major = major + 1)
    }

    /**
     * Create a new [SemVer] with the same major number and the next minor number. Patch number becomes 0.
     * Pre-release and build metadata information is not applied to the new version.
     *
     * @return next minor version
     * @throws NumberFormatException if the next minor number exceed [Int] range.
     */
    public fun nextMinor(): SemVer {
        return SemVer(major = major, minor = minor + 1)
    }

    /**
     * Create a new [SemVer] with the same major and minor number and the next patch number.
     * Pre-release and build metadata information is not applied to the new version.
     *
     * @return next patch version
     * @throws NumberFormatException if the next patch number exceed [Int] range.
     */
    public fun nextPatch(): SemVer {
        return SemVer(major = major, minor = minor, patch = patch + 1)
    }

    @Suppress("CyclomaticComplexMethod", "ReturnCount")
    override fun compareTo(other: SemVer): Int {
        if (major > other.major) return 1
        if (major < other.major) return -1
        if (minor > other.minor) return 1
        if (minor < other.minor) return -1
        if (patch > other.patch) return 1
        if (patch < other.patch) return -1

        // When major, minor, and patch are equal, a pre-release version has lower precedence than a normal version
        if (preRelease != null && other.preRelease == null) return -1
        if (preRelease == null && other.preRelease != null) return 1
        if (preRelease == null && other.preRelease == null) return 0

        // Precedence for two pre-release versions with the same major, minor, and patch version MUST be determined by
        // comparing each dot separated identifier from left to right until a difference is found
        val parts = preRelease!!.split(".")
        val otherParts = other.preRelease!!.split(".")

        val smallerSize = min(parts.size, otherParts.size)
        for (i in 0 until smallerSize) {
            val part = parts[i]
            val otherPart = otherParts[i]
            if (part == otherPart) continue
            val partIsNumeric = part.isNumeric()
            val otherPartIsNumeric = otherPart.isNumeric()

            return when {
                partIsNumeric && !otherPartIsNumeric -> -1
                !partIsNumeric && otherPartIsNumeric -> 1
                !partIsNumeric && !otherPartIsNumeric -> part.compareTo(otherPart)
                else -> try {
                    val partLong = part.toLong()
                    val otherPartLong = otherPart.toLong()
                    partLong.compareTo(otherPartLong)
                } catch (_: NumberFormatException) {
                    // When part or otherPart doesn't fit in an Long, compare as String
                    // It is not the standard way but because there are no proper BigDecimal class for Kotlin
                    // Multiplatform we have to use this way
                    part.compareTo(otherPart)
                }
            }
        }
        return when {
            parts.size == smallerSize && otherParts.size > smallerSize -> {
                // parts is ended and otherParts is not ended
                -1
            }

            parts.size > smallerSize && otherParts.size == smallerSize -> {
                // parts is not ended and otherParts is ended
                1
            }

            else -> 0
        }
    }

    /**
     * Check the version number is in initial development.
     *
     * @return true if it is in initial development.
     */
    public fun isInitialDevelopmentPhase(): Boolean = major == 0

    /**
     * Build the version name string.
     *
     * @return version name string in Semantic Versioning 2.0.0 specification.
     */
    override fun toString(): String = buildString {
        append(major)
        append('.')
        append(minor)
        append('.')
        append(patch)
        if (preRelease != null) {
            append('-')
            append(preRelease)
        }
        if (buildMetadata != null) {
            append('+')
            append(buildMetadata)
        }
    }

    private fun String.isNumeric(): Boolean = numericPattern.matches(this)

    public companion object {
        private val numericPattern = Regex("""\d+""")

        /**
         * Parse the version string to [SemVer].
         *
         * @param version version string to be parsed.
         * @return parsed [SemVer].
         * @throws IllegalArgumentException if the given string is not a valid version.
         * @throws NumberFormatException if [major], [minor], [patch] values exceed [Int] range.
         */
        @Suppress("DestructuringDeclarationWithTooManyEntries")
        public fun parse(version: String): SemVer {
            val (major, minor, patch, preRelease, buildMetadata) = (
                    FullPattern.matchEntire(version)
                        ?: throw IllegalArgumentException("Invalid version string [$version]")
                    ).destructured
            return SemVer(
                major = major.toInt(),
                minor = minor.toInt(),
                patch = patch.toIntOrNull() ?: 0,
                preRelease = preRelease.ifEmpty { null },
                buildMetadata = buildMetadata.ifEmpty { null },
            )
        }

        /**
         * Parse the version string to [SemVer].
         *
         * @param version version string to be parsed.
         * @return parsed [SemVer] or null if it cannot be parsed.
         */
        public fun parseOrNull(version: String): SemVer? = try {
            parse(version = version)
        } catch (_: IllegalArgumentException) {
            null
        }
    }
}

internal val PreReleasePattern: Regex
    get() =
        Regex("""(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*""")
internal val BuildMetadataPattern: Regex
    get() =
        Regex("""[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*""")

@Suppress("MaxLineLength")
internal val FullPattern: Regex
    get() =
        Regex(
            """(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"""
        )
