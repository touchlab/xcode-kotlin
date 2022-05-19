# Kotlin Native Xcode Support

*The xcode-kotlin plugin allows debugging of Kotlin code running in an iOS application, directly from Xcode.*

This enables a smoother development and integration experience for iOS developers using shared code from Kotlin, and a more accessible experience for larger teams where everyone may not be editing the shared code directly.

*************************************************************************
## 🔑🔑 Improving the iOS dev experience is key to KMP adoption. 

One of Touchlab’s core goals is to improve the developer experience with KMP, particularly around tooling and especially for iOS developers. We believe that improving the iOS dev experience is key to KMP adoption and we’re going to continue to work on ways to support the iOS KMP community. 

Let us know how you're using (or will use) the xcode-kotlin plugin by taking our 5-minute survey.

> [Open Touchlab Xcode Plugin User Survey](https://touchlabwaitlist.typeform.com/xcodepluginuser)
*************************************************************************


## Beta Version!!!

The CLI installer is a significant improvement over our original install process, but is also more complex. We are considering this version to be a beta release. Please let us know if you have issues! If there is a crash using the tool, it will ask if you want to upload a report. Please do. For other problems, [please file an issue in Github](https://github.com/touchlab/xcode-kotlin/issues).

We aren't anticipating any major problems, but If you cannot get the plugin to install properly, you can follow the [MANUAL_INSTALL](MANUAL_INSTALL.md) instructions as a workaround.

## Overview

The `xcode-kotlin` project consists of two main parts: the CLI manager, and the Xcode plugin itself.

### CLI

The CLI (command line interface) is an executable that is installed on your machine and manages the plugin installation(s). For existing users of `xcode-kotlin`, the CLI is new. The CLI was added to enable the following:

- Homebrew installation
- Better Xcode integration (No more "Load Bundle" popups!)
- Easier management of multiple Xcode installations
- Automatic "sync". When Xcode updates, we need to update the plugin config. This previously required updating the `xcode-kotlin` project GitHub repo, pulling, and reinstalling. The CLI can do this locally.
- Better diagnostic info and support for install issues.

### Xcode Plugin

Xcode does not generally allow plugins, but it does allow for language definitions and lldb integrations. There is no official process for including these things, which is why the CLI is necessary. However, lldb is an open standard and debugging integrations are a common use case. We share, and contribute to, the [official Kotlin language lldb extensions](https://github.com/JetBrains/kotlin/blob/master/kotlin-native/llvmDebugInfoC/src/scripts/konan_lldb.py).

## Installation

First you need to install the CLI that takes care of installing the plugin into Xcode. The CLI is available through Homebrew:

```shell
brew install xcode-kotlin
```

Once installed, run the CLI:

```shell
xcode-kotlin install
```

This will install the plugin with support for all of your currently installed Xcode installations.

## Manual Install

If needed, you can install manually. See [MANUAL_INSTALL](MANUAL_INSTALL.md).

## Sync

When you update Xcode versions, you'll need to enable the plugin for that version. Run:

```shell
xcode-kotlin sync
```

This process adds the UUID for the new Xcode version to the local plugin configuration. For users familiar with earlier versions of `xcode-kotlin`, Xcode updates would previously require an [update from GitHub](https://github.com/touchlab/xcode-kotlin/pull/37/files).

## Plugin Usage

If properly set up, you should be able to add Kotlin source to Xcode, set up breakpoints, and step through code. To add Kotlin source to Xcode, follow these steps:

1. Add a New Group to the Xcode project.
2. Add Files to the newly created group (Kotlin Debug in this instance).
3. Select the folders in the Kotlin library that are directly relevant to the iOS build, which will usually be `commonMain` and `iosMain`. Make sure "Copy items into destination group's folder (if needed)" is unchecked.

<img src="https://tl-navigator-images.s3.us-east-1.amazonaws.com/docimages/2022-04-27_08-31-XcodeKotlinFileReferencesSteps.png" alt="XcodeKotlinFileReferencesSteps" style="zoom: 25%;" />

When you're done, your Xcode project structure should look something like this:

![kotlinsources](https://tl-navigator-images.s3.us-east-1.amazonaws.com/docimages/2022-04-27_09-03-kotlinsources.png)

### Sample

The project used as an example above is [KaMPKit](https://github.com/touchlab/KaMPKit/). Check it out if you want to see a project that already includes Kotlin file references in Xcode. It's an excellent template for Kotlin multiplatform mobile projects.

## Troubleshooting

If you're having any issues, try reinstalling the plugin:

```shell
xcode-kotlin uninstall
xcode-kotlin install
```

If it doesn't fix the issue, run:

```shell
xcode-kotlin info
```

This will show you status of the plugin and a list of found Xcode installations. If the Xcode you want to use isn't listed you can run the `sync` command and provide it with paths to Xcode installations to add support for:

```
xcode-kotlin sync /Volumes/ExternalVolume1/Xcode.app
```

If the issue still persists, open a new GitHub issue and include the output of the `info` command.

## About

Our Xcode plugin incorporates the work of other brave souls around the web exploring the undocumented corners of Xcode. See [ABOUT](ABOUT.md).

***********************
> ## Touchlab's Hiring!
>
> We're looking for a Mobile Developer, with Android/Kotlin experience, who is eager to dive into Kotlin Multiplatform Mobile (KMM) development. Come join the remote-first team putting KMM in production. [More info here](https://go.touchlab.co/careers-gh).
