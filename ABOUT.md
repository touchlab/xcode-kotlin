# Sources

Setting up the Plugin has been an amalgam of various source projects, as Xcode "Plugins" are undocumented. The most significant piece, the language color file came from other color files shipped with Xcode. Xcode plugin file from [GraphQL](https://github.com/apollographql/xcode-graphql/blob/master/GraphQL.ideplugin/Contents/Resources/GraphQL.xcplugindata)

LLDB formatting originally comes from the Kotlin/Native project, source [konan_lldb.py](https://github.com/JetBrains/kotlin/blob/master/kotlin-native/llvmDebugInfoC/src/scripts/konan_lldb.py), although the way data is grabbed has been heavily modified to better support an interactive debugger.

# llvm/lldb Scripts

Our Xcode plugin uses standard lldb integrations. The Kotlin language ships an  [lldb script](https://github.com/JetBrains/kotlin/blob/master/kotlin-native/llvmDebugInfoC/src/scripts/konan_lldb.py) to format Kotlin objects for debugging. It is the same script used across tools in the Kotlin ecosystem for debugging Kotlin native. The performance of the debugger (and lack thereof) is directly tied to this script. We have contributed optimizations in the past, but there is certainly more that can be done. If you have interesting ideas, please submit a PR and we'll see if the main Kotlin team is interested as well...

# Possible Future Stuff

Check out the [Discussions](https://github.com/touchlab/xcode-kotlin/discussions/).

