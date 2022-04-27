@file:Suppress("UnstableApiUsage")

plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.kotlin.plugin.serialization)
}

group = "co.touchlab"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

kotlin {
    listOf(macosX64(), macosArm64()).forEach {
        it.binaries {
            executable {
                entryPoint = "co.touchlab.xcode.cli.main"
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
        }
    }
}

tasks.register<Exec>("assembleReleaseExecutableMacos") {
    dependsOn("linkReleaseExecutableMacosX64", "linkReleaseExecutableMacosArm64")
    commandLine("lipo", "-create", "-o", "xcode-kotlin", "bin/macosX64/releaseExecutable/xcode-kotlin.kexe", "bin/macosArm64/releaseExecutable/xcode-kotlin.kexe")
    workingDir = buildDir
    group = "build"
    description = "Builds an universal macOS binary for both x86_64 and arm64 architectures."
}