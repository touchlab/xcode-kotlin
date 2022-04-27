# Manual Installation

For advanced users, or if you have issues, you may want to install manually. There are 2 parts to Kotlin support: 1) debugging support and 2) language color and style formatting.

You need to tell Xcode that `*.kt` files are source files, and run an lldb formatter script when debugging starts. Look at the `setup.sh` script in the `legacy` directory and see the folders where those parts go.

*NOTE:* The `setup.sh` script in the legacy folder is not runnable. It exists only for reference.

## Xcode Updates

When Xcode is updated, you may need to add the UUID to `Kotlin.ideplugin/Contents/Info.plist`. To find the UUID of your version of Xcode, run the following:

```
defaults read /Applications/Xcode.app/Contents/Info DVTPlugInCompatibilityUUID
```

Info [from here](https://www.mokacoding.com/blog/xcode-plugins-update/)