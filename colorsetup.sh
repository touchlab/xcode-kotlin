#!/usr/bin/env bash

###################
# LANGUAGE SPEC
###################

spec_dir=/Applications/Xcode.app/Contents/SharedFrameworks/SourceModel.framework/Versions/A/Resources/LanguageSpecifications

cp Kotlin.xclangspec $spec_dir

meta_dir=/Applications/Xcode.app/Contents/SharedFrameworks/SourceModel.framework/Versions/A/Resources/LanguageMetadata

cp Xcode.SourceCodeLanguage.Kotlin.plist $meta_dir