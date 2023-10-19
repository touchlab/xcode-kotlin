package co.touchlab.xcode.cli

import co.touchlab.kermit.LogWriter
import co.touchlab.kermit.Severity
import kotlinx.cinterop.ExperimentalForeignApi
import platform.posix.fflush
import platform.posix.fprintf
import platform.posix.stderr

class EchoWriter: LogWriter() {
    override fun log(severity: Severity, message: String, tag: String, throwable: Throwable?) {
        val printString: (String) -> Unit = when (severity) {
            Severity.Verbose, Severity.Debug -> return
            Severity.Info -> { string -> println(string) }
            Severity.Warn -> { string -> println("WARN: $string") }
            Severity.Error, Severity.Assert -> @OptIn(ExperimentalForeignApi::class) { string ->
                fprintf(stderr, string)
                fflush(stderr)
            }
        }

        printString(message)
        throwable?.let {
            printString(it.stackTraceToString())
        }
    }
}
