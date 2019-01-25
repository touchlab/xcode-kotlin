#!/usr/bin/env bash

plugins_dir=~/Library/Developer/Xcode/Plug-ins/
spec_dir=~/Library/Developer/Xcode/Specifications
lldb_format="command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/kotlin_lldb.py"

# Create Plug-ins directory if it doesn't exist
if [ ! -d "$plugins_dir" ]; then
	mkdir $plugins_dir
fi

# Create Specifications directory if it doesn't exist
if [ ! -d "$spec_dir" ]; then
	mkdir $spec_dir
fi

cp -r Kotlin.ideplugin $plugins_dir
cp Kotlin.xclangspec $spec_dir

if grep --quiet	-s kotlin_lldb ~/.lldbinit
then
    # code if found
		echo "kotlin_lldb.py found in ~/.lldbinit, which means this was probably set up previously. You may want to manually check ~/.lldbinit"
else
    # code if not found
		echo $lldb_format >> ~/.lldbinit
fi
