# Building

The xcode-kotlin plugin is written in **Kotlin**. It uses 
[Kotlin/Native](https://kotlinlang.org/docs/native-overview.html) for compiling Kotlin code to native binaries. 

Building environment: **IntelliJ IDEA**


## Libraries

- [kotlinx-cli](org.jetbrains.kotlinx:kotlinx-cli) - a generic command-line parser used to create user-friendly and flexible command-line interfaces
- [kotlinx-serialization-json](https://kotlinlang.org/docs/serialization.html) - JSON serialization for Kotlin projects
- [kotlinx-coroutines](https://github.com/Kotlin/kotlinx.coroutines) - library support for Kotlin coroutines with multiplatform support
- [Kermit](https://github.com/touchlab/Kermit) - logging utility with composable log outputs

## Project structure

In the `command` directory the commands users can call are implemented: *info*, *install*, *sync* and *uninstall*. 
Each has an `execute` function with the implementation, that calls classes like `Installer` or `Uninstaller`.
- `BaseXcodeListSubcommand` is an abstract class overriden by the following classes (Info, Install and Sync). It 
provides them with a protected method for getting a list of Xcode installations.
- `Info` checks for an available update or if the plugin is not yet installed, writes information about the plugin to 
the console, such as installed and bundles versions, if Language spec and LLDB is installed and if LLDB for Xcode has 
been initialized, also Xcode version and the plugin compatibility.
- `Install` checks for current version and offers updating, reinstalling or downgrading if it is already installed or 
installs it if not.
- `Sync` adds IDs of Xcode installations to the currently installed Xcode Kotlin plugin.
- `Uninstall` uninstalls the plugin.

In the `util` directory are, as the name suggests, util classes.
- `Console` provides convenience functions for prompting user for confirmation or value and printing output to the 
console.
- `CrashHelper` provides functions for logging, capturing and uploading errors (crash reports).
- `File` is a class for holding a file path and providing methods for working with a file.
- `Path` holds a string value and provides methods for appending and deleting path components and resolving sym links. 
It also provides convenience methods for creating Paths to home, work, binary and data directories in its companion 
object.
- `PropertyList` is a class for converting to and from Swift classes.
- `Shell` is a helper for executing shell tasks.

The other classes in the `cli` directory are mainly managers and helpers that provide methods for installing and 
uninstalling various parts of the plugin.
- `Installer` has an `installAll` method for calling install on all the managers.
- `LangSpecManager` provides `install` and `uninstall` methods and `isInstalled` check for the Kotlin.xclangspec.
- `LLDBInitManager` provides `install` and `uninstall` methods and `isInstalled` and `sourcesMainLlvmInit` checks for 
the LLDB init.
- `PluginManager` provides `install`, `sync` and `uninstall` methods,`isInstalled` check and `bundledVersion`, 
`installedVersion` and `targetSupportedXcodeUUIds` properties for the plugin.
- `Uninstaller` has an `uninstallAll` method for calling uninstall on all the managers.
- `XcodeHelper` provides methods for interacting with Xcode installations: `ensureXcodeNotRunning` to check and 
optionally shut down running Xcode instances, `allXcodeInstallations` that returns a list of found Xcode installations, 
`addKotlinPluginToDefaults` for adding a plugin to allowed list in Xcode defaults and `removeKotlinPluginFromDefaults` 
for removing it.

In `build.gradle` there are two gradle tasks added: `assembleReleaseExecutableMacos` for building a universal macOS 
binary and `preparePlugin` for preparing the plugin and language specification to build dir.

This project uses Object classes instead of dependency injection (DI) because of its small size.