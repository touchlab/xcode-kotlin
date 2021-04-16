#!/usr/bin/env bash

# Use this script for Xcode 11.

###################
# This script is specifically for development of the plugin. Currently, the goal is just to move the new formatting scripts
# into place. Much faster round trip than killing Xcode, etc.
# Do *not* use this script if you're not actively developing the plugin.
###################

###################
# DEFINITIONS
###################

service='Xcode'
plugins_dir=~/Library/Developer/Xcode/Plug-ins

###################
# CREATE PLUG-IN
###################

echo "Creating new Kotlin plugin"
mkdir -p $plugins_dir
cp -r Kotlin.ideplugin $plugins_dir

###################
# LLDB DEFINITIONS
###################

lldb_config="command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/konan_lldb_config.py"
lldb_format="command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/konan_lldb.py"

if grep --quiet	-s konan_lldb ~/.lldbinit-Xcode
then
  # code if found
  echo "konan_lldb.py found in ~/.lldbinit-Xcode"
else
  # code if not found
  echo $lldb_config >> ~/.lldbinit-Xcode
  echo $lldb_format >> ~/.lldbinit-Xcode
fi
