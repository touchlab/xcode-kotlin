# Manual Installation

For advanced users, or if you have issues, you may want to install manually. There are 2 parts to Kotlin support: 1) debugging support and 2) language color and style formatting.

To follow the original install process, [clone the repo](https://github.com/touchlab/xcode-kotlin) and check out the [legacy branch](https://github.com/touchlab/xcode-kotlin/tree/legacy). You can follow the README instructions there. Basically, run:

```shell
./setup.sh
```

Alternatively, to manually install, you can follow the steps in  `setup.sh`. You'll see the folders that the parts of the Xcode plugin need to be copied into.

If the Xcode version is newer than 13.3, you'll likely need to find and append the UUID for that version to the `Info.plist` file.

See the next section, [Xcode Updates](#xcode-updates), for instructions on getting the UUID. See [this merged PR](https://github.com/touchlab/xcode-kotlin/pull/46/files) for an example of appending the UUID to the `Info.plist` file.

## Xcode Updates

When Xcode is updated, you may need to add the UUID to `Kotlin.ideplugin/Contents/Info.plist`. To find the UUID of your version of Xcode, run the following:

```
defaults read /Applications/Xcode.app/Contents/Info DVTPlugInCompatibilityUUID
```

Info [from here](https://www.mokacoding.com/blog/xcode-plugins-update/)

The new CLI tool manages all of that locally, so it's generally a better idea to use that. See the main [README](README.md) for more info.