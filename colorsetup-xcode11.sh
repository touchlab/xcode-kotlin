#!/usr/bin/env bash

###################
# LANGUAGE SPEC
###################

xcode_developer_dir=$(xcode-select --print-path)

## Default is /Applications/Xcode.app/Contents
xcode_content_dir=$(dirname "$xcode_developer_dir")

spec_dir=$xcode_content_dir/SharedFrameworks/SourceModel.framework/Versions/A/Resources/LanguageSpecifications

cp Kotlin.xclangspec $spec_dir

meta_dir=$xcode_content_dir/SharedFrameworks/SourceModel.framework/Versions/A/Resources/LanguageMetadata

cp Xcode.SourceCodeLanguage.Kotlin.plist $meta_dir