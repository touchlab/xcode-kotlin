### Xcode 11

For debugging support in Xcode 11, run the installation script:

```
./setup-xcode11.sh
```

Xcode 11 introduced several breaking changes from earlier versions, and some resolutions are still outstanding. If you're using Xcode 11, you need to move some files into a protected area. Some users may not want to do this, and may possibly not have permissions to do this. You'll need to run the formatting support script with sufficient permissions, which generally means `sudo`.

```
sudo ./colorsetup-xcode11.sh
```

*You can still debug Kotlin without formatting support, just FYI. This step is not required.*