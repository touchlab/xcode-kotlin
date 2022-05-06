package co.touchlab.xcode.cli

import co.touchlab.kermit.Logger
import co.touchlab.xcode.cli.util.Console
import co.touchlab.xcode.cli.util.File
import co.touchlab.xcode.cli.util.Path
import co.touchlab.xcode.cli.util.kt
import co.touchlab.xcode.cli.util.objc
import platform.Foundation.containsString
import platform.Foundation.stringByReplacingOccurrencesOfString

object LLDBInitManager {
    private val pluginInitFile = File(PluginManager.pluginTargetFile.path / "Contents" / "Resources" / "lldbinit")
    private val sourcePluginInit = "command source ${pluginInitFile.path}"
    private val sourceMainLlvmInit = "command source ~/.lldbinit"
    private val lldbInitFile = File(Path.home / ".lldbinit")
    private val lldbInitXcodeFile = File(Path.home / ".lldbinit-Xcode")
    private val logger = Logger.withTag("LLDBInitManager")

    val isInstalled: Boolean
        get() {
            if (!lldbInitXcodeFile.exists()) {
                return false
            }
            return lldbInitXcodeFile.stringContents().containsString(sourcePluginInit)
        }

    val sourcesMainLlvmInit: Boolean
        get() {
            if (!lldbInitXcodeFile.exists()) {
                return true
            }
            return lldbInitXcodeFile.stringContents().containsString(sourceMainLlvmInit)
        }

    fun install() {
        check(!isInstalled) { "LLDB init is already installed" }

        val oldContents = when {
            lldbInitXcodeFile.exists() -> {
                logger.v { "${lldbInitXcodeFile.path} exists, will append LLDB init into it." }
                lldbInitXcodeFile.stringContents().kt
            }
            lldbInitFile.exists() -> {
                Console.echo("""
                    This installer will create a new file at '~/.lldbinit-Xcode'. This file takes precedence over the '~/.lldbinit' file. 
                    To keep using configuration from '~/.lldbinit' file, it needs to be sourced by the newly created '~/.lldbinit-Xcode' file.
                """.trimIndent())
                if (Console.confirm("Do you want to source the '~/.lldbinit' file? y/n: ")) {
                    logger.v { "Will source ~/.lldbinit." }
                    sourceMainLlvmInit
                } else {
                    ""
                }
            }
            else -> {
                ""
            }
        }

        val oldAndNewContentsSeparator = if (!oldContents.endsWith("\n")) "\n" else ""
        val newContents = oldContents + oldAndNewContentsSeparator + sourcePluginInit
        logger.v { "Saving new LLDB init to ${lldbInitXcodeFile.path}." }
        lldbInitXcodeFile.write(newContents.objc)
    }

    fun uninstall() {
        if (isInstalled) {
            logger.v { "LLDB init script found, removing." }
            val oldContents = lldbInitXcodeFile.stringContents()
            val newContents = oldContents.stringByReplacingOccurrencesOfString(target = sourcePluginInit, withString = "")
            lldbInitXcodeFile.write(newContents.objc)
        }
        Legacy.uninstall()
    }

    object Legacy {
        private val logger = Logger.withTag("LLDBInitManager")
        private val legacyImport = """
            command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/konan_lldb_config.py
            command script import ~/Library/Developer/Xcode/Plug-ins/Kotlin.ideplugin/Contents/Resources/konan_lldb.py
        """.trimIndent()

        val isInstalled: Boolean
            get() {
                if (!lldbInitXcodeFile.exists()) {
                    return false
                }
                return lldbInitXcodeFile.stringContents().containsString(legacyImport)
            }

        fun uninstall() {
            if (isInstalled) {
                logger.v { "Legacy LLDB script initialization found, removing." }
                val oldContents = lldbInitXcodeFile.stringContents()
                val newContents = oldContents.stringByReplacingOccurrencesOfString(target = legacyImport, withString = "")
                lldbInitXcodeFile.write(newContents.objc)
            }
        }
    }
}