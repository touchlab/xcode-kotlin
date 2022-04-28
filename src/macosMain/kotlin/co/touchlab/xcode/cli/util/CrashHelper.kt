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

    private fun capture(e: Throwable): String = StringBuilder().apply {
        if (logEntries.isNotEmpty()) {
            append("BREADCRUMBS\n===========\n\n")
            append(logEntries.joinToString("\n"))
            append("\n\n")
        }

        append("FINAL CRASH\n===========\n\n")
        append(e.getStackTrace().joinToString("\n"))
    }.toString()

    data class LogEntry(val severity: Severity, val message: String, val tag: String, val throwable: Throwable?) {
        override fun toString(): String = StringBuilder().apply {
            append("$severity - $tag - $message")
            throwable?.let<Throwable, Unit> {
                append("\n")
                append(it.getStackTrace().joinToString("\n"))
            }
        }.toString()
    }
}