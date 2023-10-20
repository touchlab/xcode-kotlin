@file:Suppress("UnstableApiUsage")

import org.apache.tools.ant.filters.ReplaceTokens

plugins {
    alias(libs.plugins.gradle.doctor)
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.kotlin.plugin.serialization)
}

group = "co.touchlab"
version = "1.3.0"

kotlin {
    listOf(macosX64(), macosArm64()).forEach {
        it.binaries {
            executable {
                entryPoint = "co.touchlab.xcode.cli.main"

                runTask?.run {
                    val args = providers.gradleProperty("runArgs")
                    args(args.getOrElse("").split(' '))

                    standardOutput = System.out
                    errorOutput = System.err
                }
            }
        }
    }

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(libs.kotlinx.cli)
                implementation(libs.kotlinx.serialization.json)
                implementation(libs.kermit)
                implementation(libs.kotlinx.coroutines.core)
            }
        }
        val macosMain by creating {
            dependsOn(commonMain)
        }
        val macosX64Main by getting {
            dependsOn(macosMain)
        }
        val macosArm64Main by getting {
            dependsOn(macosMain)
        }

        val commonTest by getting {
            dependencies {
                implementation(kotlin("test"))
            }
        }
        val macosTest by creating {
            dependsOn(commonTest)
        }
        val macosX64Test by getting {
            dependsOn(macosTest)
        }
        val macosArm64Test by getting {
            dependsOn(macosTest)
        }

        all {
            languageSettings.optIn("kotlinx.cli.ExperimentalCli")
            languageSettings.optIn("kotlinx.cinterop.BetaInteropApi")
            languageSettings.optIn("kotlin.experimental.ExperimentalNativeApi")
        }
    }
}

tasks.register<Exec>("assembleReleaseExecutableMacos") {
    dependsOn("linkReleaseExecutableMacosX64", "linkReleaseExecutableMacosArm64")
    commandLine(
        "lipo", "-create", "-o", "xcode-kotlin",
        "bin/macosX64/releaseExecutable/xcode-kotlin.kexe",
        "bin/macosArm64/releaseExecutable/xcode-kotlin.kexe",
    )
    workingDir(layout.buildDirectory)
    group = "build"
    description = "Builds an universal macOS binary for both x86_64 and arm64 architectures."
}

tasks.register<Copy>("preparePlugin") {
    group = "build"
    description = "Prepares plugin and language specification to build dir."

    from(layout.projectDirectory.dir("data")) {
        include("Kotlin.ideplugin/**", "Kotlin.xclangspec")
        filter(
            ReplaceTokens::class,
            "tokens" to mapOf(
                "version" to version,
            )
        )
    }
    into(layout.buildDirectory.dir("share"))
}
