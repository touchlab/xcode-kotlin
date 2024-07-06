plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.skie)
    application
}

version = "1.0"

kotlin {
    jvm()
    listOf(
        macosArm64(),
        macosX64(),
    ).forEach {
        it.binaries.framework {
            isStatic = true
        }
    }

    sourceSets {
        commonMain.dependencies {
//            implementation(libs.coroutines.core)
        }
    }
}

skie {
    isEnabled = true
}

tasks.register<Exec>("compileSwift") {
    group = "build"

    dependsOn("linkDebugFrameworkMacosArm64")

    doFirst {
        workingDir.mkdirs()
    }

    workingDir(layout.buildDirectory.dir("swift"))
    commandLine(
        "/usr/bin/xcrun",
        "swiftc",
        "-g",
        "-F",
        layout.projectDirectory.dir("build/bin/macosArm64/debugFramework"),
        "-o",
        "app",
        "-Xlinker",
        "-dead_strip",
        layout.projectDirectory.file("main.swift")
    )
}
