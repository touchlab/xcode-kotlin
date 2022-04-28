# Manual Installation

For advanced users, or if you have issues, you may want to install manually. There are 2 parts to Kotlin support: 1) debugging support and 2) language color and style formatting.

Look at the [legacy branch](https://github.com/touchlab/xcode-kotlin/tree/legacy) in the `xcode-kotlin` Github repo to see the original install script `setup.sh`. You'll see the folders that the parts of the Xcode plugin need to be copied into.

If the Xcode version is newer than 13.3, you'll likely need to find and append the UUID for that version to the `Info.plist` file.

See the next section, [Xcode Updates](#xcode-updates), for instructions on getting the UUID. See [this merged PR](https://github.com/touchlab/xcode-kotlin/pull/46/files) for an example of appending the UUID to the `Info.plist` file.

## Xcode Updates

When Xcode is updated, you may need to add the UUID to `Kotlin.ideplugin/Contents/Info.plist`. To find the UUID of your version of Xcode, run the following:

```
defaults read /Applications/Xcode.app/Contents/Info DVTPlugInCompatibilityUUID
```

Info [from here](https://www.mokacoding.com/blog/xcode-plugins-update/)