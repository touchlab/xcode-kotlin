package co.touchlab.xcode.cli.util

import co.touchlab.kermit.LogWriter
import co.touchlab.kermit.Severity
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.runBlocking
import platform.Foundation.*
import platform.Foundation.NSURLSessionConfiguration.Companion.defaultSessionConfiguration

class CrashHelper : LogWriter() {
    private val logEntries = mutableListOf<LogEntry>()

    override fun log(severity: Severity, message: String, tag: String, throwable: Throwable?) {
        logEntries.add(LogEntry(severity, message, tag, throwable))
    }

    fun upload(e: Throwable) {
        upload(capture(e))
    }

    private fun upload(crashReport: String) {
        val url: NSURL = NSURL.URLWithString("https://api.touchlab.dev/crash/report")!!
        val request = NSMutableURLRequest.requestWithURL(url).apply {
            setHTTPMethod("POST")
            setValue("text/plain", "Content-Type")
            setHTTPBody((crashReport as NSString).dataUsingEncoding(NSUTF8StringEncoding))
        }

        val uploadComplete = CompletableDeferred<Unit>()
        val session = NSURLSession
            .sessionWithConfiguration(defaultSessionConfiguration)
            .dataTaskWithRequest(request) { _, _, _ ->
                uploadComplete.complete(Unit)
            }

        runBlocking {
            session.resume()
            uploadComplete.await()
        }
    }

    private fun capture(e: Throwable): String {
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

        return out
    }

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
