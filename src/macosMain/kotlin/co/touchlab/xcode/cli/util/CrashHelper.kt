package co.touchlab.xcode.cli.util

import co.touchlab.kermit.LogWriter
import co.touchlab.kermit.Severity

class CrashHelper : LogWriter() {
    private val logEntries = mutableListOf<LogEntry>()

    fun uploadPreviousCrashIfNeeded() {
        if (needsUpload()) upload()
    }

    fun upload() {
        // Remember to delete the crash report file on success...
    }

    fun capture(e: Throwable) {
        deleteCrashReportFile()

        var out = ""

        if (!logEntries.isEmpty()) {
            out += "BREADCRUMBS\n===========\n\n"
            logEntries.forEach {
                out += it.toString() + "\n"
            }
            out += "\n\n"
        }

        out += "FINAL CRASH\n===========\n\n"
        out += toStacktraceString(e)

        crashReportFile().write(out.objc)
    }

    override fun log(severity: Severity, message: String, tag: String, throwable: Throwable?) {
        logEntries.add(LogEntry(severity, message, tag, throwable))
    }

    private fun deleteCrashReportFile() {
        try {
            crashReportFile().delete()
        } catch (e: Exception) {
            // Do nothing
        }
    }

    private fun needsUpload() =
        crashReportFile().exists()

    private fun crashReportFile() =
        File(Path.workDir.appendingPathComponent("crash-report.txt"))

    data class LogEntry(val severity: Severity, val message: String, val tag: String, val throwable: Throwable?) {
        override fun toString(): String {
            var out = "$severity - $tag - $message"
            throwable?.let {
                out += "\n${toStacktraceString(it)}"
            }
            return out
        }
    }
}

private fun toStacktraceString(e: Throwable): String {
    var stacktrace = ""
    e.getStackTrace().forEach {
        stacktrace += it + "\n"
    }
    return stacktrace
}
