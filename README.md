# Kotlin Native Xcode Support

Plugin to facilitate debugging iOS applications using Kotlin Native in Xcode.
Defines Kotlin files as source code, with basic highlighting. Allows you to
set breakpoints and includes llvm support to view data in the debug window.

## Blog post and live demo

Check out the [blog post and sign up for the live video demo](https://medium.com/@kpgalligan/kotlin-xcode-plugin-64f52ff8dc2a) on Friday 4/26 (3pm EST).

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
command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/konan_lldb.py
```

### Usage

If properly set up, you should be able to add Kotlin source to Xcode, set up breakpoints, and step through code.
Be careful not to have Kotlin source added to the iOS Bundle output.

To help automate adding Kotlin source, check out the [Kotlin Xcode Sync](https://github.com/touchlab/KotlinXcodeSync) Gradle plugin.

### Sample

The [Droidcon NYC](https://github.com/touchlab/DroidconKotlin/) app has both the Xcode Gradle sync and Xcode projects enabled for debugging.

### Sources

Setting up the Plugin has been an amalgam of various source projects, as Xcode "Plugins"
are undocumented. The most significant piece, the language color file, came from other color 
files shipped with Xcode. Xcode plugin file from [GraphQL](https://github.com/apollographql/xcode-graphql/blob/master/GraphQL.ideplugin/Contents/Resources/GraphQL.xcplugindata)

LLDB formatting originally comes from the Kotlin/Native project, source [konan_lldb.py](https://github.com/JetBrains/kotlin-native/blob/dbb162a4b523071f31913e888e212df344a1b61e/llvmDebugInfoC/src/scripts/konan_lldb.py), although the way data is grabbed has been heavily modified to better
support an interactive debugger.

## Xcode 11 Beta

The current version of the plugin will still allow you to add breakpoints and run the debugger, but source code highlighting is not yet functional. When Xcode 11 releases
we'll dig back into the situation.

## Coming Soon

### LLDB Formatter

The plugin itself relies on the lldb python formatter which was mostly adapted from the lldb formatter that comes with Kotlin Native. That script was really written for command line use. In an interactive context (like this plugin) the performance isn't great. Most of our changes are around optimizations. However, there are ongoing changes both to the underlying script and (possibly) to the memory layout of Kotlin Native itself at runtime.

The script in this plugin could use a refresh with a more recent base version from Kotlin Native, and if possible, refactor the optimizations to be as close to "stock" as possible, to make future updates easier.

The formatter also takes a very basic approach to data formatting. Lists are capped at 20 entries to avoid super long refreshes. Maps show their underlying data structures, but could get custom formatting (for example). There is a lot that could be done.

We currently can't get some things like class name. This could be enabled with moderate additions to Kotlin Native debug facilities.

### Debug aligning

The breakpoints and runtime *usually* line up, but they can get weird. This is especially true around things like lambdas. This *may* be related to what the llvm compiler is writing, or it may simply be an artifact of how Xcode is setting breakpoints. We'll need reports and repros of code that confuses the debugger to see if that can be improved.

### Color File

The color definition is basically Java's with minor additions. This could be better adapted to Kotlin.

### Install

It's a bash script, which works, but does not take into account non-standard install directories and various other possible config options. This could be improved.
