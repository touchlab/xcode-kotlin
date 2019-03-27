# Kotlin Native Xcode Support

Plugin to facilitate debugging iOS applications using Kotlin Native in Xcode.
Defines Kotlin files as source code, with basic highlighting. Allows you to
set breakpoints and includes llvm support to view data in the debug window.

> [What is Kotlin Multiplatform and what are we working on?](https://touchlab.co/)

## Installation

### Watch Video

[![Kotlin Xcode Setup](https://img.youtube.com/vi/CqzSyWI_esY/0.jpg)](https://www.youtube.com/watch?v=CqzSyWI_esY)

### Setup script

Run the following command in your terminal:

```
./setup.sh
```

### Manual installation

Please note that if you are running Xcode 8 the `Plug-ins` and `Specifications` directories might not exist.

- Copy the `Kotlin.ideplugin` directory to `~/Library/Developer/Xcode/Plug-ins/`:

	```
	cp -r Kotlin.ideplugin ~/Library/Developer/Xcode/Plug-ins/
	```
- Copy the `Kotlin.xclangspec` file to `~/Library/Developer/Xcode/Specifications`:

	```
	cp Kotlin.xclangspec ~/Library/Developer/Xcode/Specifications/
	```

lldb formatting support is provided by konan_lldb.py. The setup script will add
the path to `~/.lldbinit`. You can manually load this script at the lldb prompt
with

```
command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/kotlin_lldb.py
```

### Usage

If properly set up, you should be able to add Kotlin source to Xcode, set up breakpoints, and step through code.
Be careful not to have Kotlin source added to the iOS Bundle output.

To help automate adding Kotlin source, check out the [Kotlin Xcode Sync](https://github.com/touchlab/KotlinXcodeSync) Gradle plugin.

### Sources

Setting up the Plugin has been an amalgam of various source projects, as Xcode "Plugins"
are undocumented. The most significant piece, the language color file, came from other color 
files shipped with Xcode. Xcode plugin file from [GraphQL](https://github.com/apollographql/xcode-graphql/blob/master/GraphQL.ideplugin/Contents/Resources/GraphQL.xcplugindata)

LLDB formatting originally comes from the Kotlin/Native project, source [konan_lldb.py](https://github.com/JetBrains/kotlin-native/blob/dbb162a4b523071f31913e888e212df344a1b61e/llvmDebugInfoC/src/scripts/konan_lldb.py), although the way data is grabbed has been heavily modified to better
support an interactive debugger.

