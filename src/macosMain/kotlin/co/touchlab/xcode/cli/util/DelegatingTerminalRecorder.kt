package co.touchlab.xcode.cli.util

import com.github.ajalt.mordant.rendering.AnsiLevel
import com.github.ajalt.mordant.terminal.PrintRequest
import com.github.ajalt.mordant.terminal.TerminalInfo
import com.github.ajalt.mordant.terminal.TerminalInterface
import com.github.ajalt.mordant.terminal.TerminalRecorder

class DelegatingTerminalRecorder(
    val delegate: TerminalInterface,
): TerminalInterface {
    val recorder = TerminalRecorder()

    override fun completePrintRequest(request: PrintRequest) {
        delegate.completePrintRequest(request)
        recorder.completePrintRequest(request)
    }

    override fun info(
        ansiLevel: AnsiLevel?,
        hyperlinks: Boolean?,
        outputInteractive: Boolean?,
        inputInteractive: Boolean?
    ): TerminalInfo = delegate.info(ansiLevel, hyperlinks, outputInteractive, inputInteractive)

    override fun readLineOrNull(hideInput: Boolean): String? = delegate.readLineOrNull(hideInput)
}
