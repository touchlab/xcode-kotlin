#!/usr/bin/env bash

###################
# PLUGINS DIRECTORY
###################

plugins_dir=~/Library/Developer/Xcode/Plug-ins/

if [ ! -d "$plugins_dir" ]; then
	mkdir -p $plugins_dir
fi

cp -r Kotlin.ideplugin $plugins_dir

###################
# LANGUAGE SPEC
###################

spec_dir=~/Library/Developer/Xcode/Specifications

if [ ! -d "$spec_dir" ]; then
	mkdir -p $spec_dir
fi

cp Kotlin.xclangspec $spec_dir

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
