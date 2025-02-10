@file:Suppress("invisible_reference", "invisible_member")

package co.touchlab.xcode.cli.util

import com.github.ajalt.mordant.internal.STANDARD_TERM_INTERFACE
import com.github.ajalt.mordant.terminal.Terminal
import com.github.ajalt.mordant.terminal.YesNoPrompt
import com.github.ajalt.mordant.terminal.danger
import com.github.ajalt.mordant.terminal.info
import com.github.ajalt.mordant.terminal.muted
import com.github.ajalt.mordant.terminal.success
import com.github.ajalt.mordant.terminal.warning

object Console {
    val terminalRecorder = DelegatingTerminalRecorder(delegate = STANDARD_TERM_INTERFACE)
    val terminal = Terminal(terminalInterface = terminalRecorder)

    fun echo(text: String = "") {
        terminal.println(text)
    }

    fun confirm(text: String): Boolean {
        while (true) {
            val result = YesNoPrompt(text, terminal).ask()
            if (result != null) {
                return result
            }
        }
    }

    fun muted(message: String) {
        terminal.muted(message)
    }

    fun info(message: String) {
        terminal.info(message)
    }

    fun warning(message: String) {
        terminal.warning(message)
    }

    fun danger(message: String) {
        terminal.danger(message, stderr = true)
    }

    fun success(message: String) {
        terminal.success(message)
    }
}
