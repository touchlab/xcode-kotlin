import org.jetbrains.kotlin.gradle.ExperimentalKotlinGradlePluginApi
import org.jetbrains.kotlin.gradle.plugin.KotlinSourceSetTree

plugins {
    alias(libs.plugins.kotlin.multiplatform)
}

version = "1.0"

kotlin {
    listOf(
        macosArm64(),
        macosX64(),
    ).forEach {
        it.binaries.executable()
    }

    sourceSets {
        commonMain.dependencies {
            implementation(libs.coroutines.core)
        }
    }
}
