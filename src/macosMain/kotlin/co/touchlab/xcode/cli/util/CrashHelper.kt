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
        val tagQuery = "?tag=xcode-kotlin" + if (Platform.isDebugBinary) "-DEBUG" else ""
        val url = "https://api.touchlab.dev/crash/report$tagQuery".let { urlString ->
            checkNotNull(NSURL.URLWithString(urlString)) {
                "Couldn't construct NSURL from $urlString"
            }
        }
        val request = NSMutableURLRequest.requestWithURL(url).apply {
            setHTTPMethod("POST")
            setValue("text/plain", "Content-Type")
            setHTTPBody(crashReport.objc.dataUsingEncoding(NSUTF8StringEncoding))
        }

        val uploadComplete = CompletableDeferred<Unit>()
        val session = NSURLSession
            .sessionWithConfiguration(defaultSessionConfiguration)
            .dataTaskWithRequest(request) { _, _, error ->
                if (error != null) {
                    uploadComplete.completeExceptionally(CrashReportUploadException(error))
                } else {
                    uploadComplete.complete(Unit)
                }
            }

        runBlocking {
            session.resume()
            uploadComplete.await()
        }
    }

    private fun capture(e: Throwable): String = buildString {
        if (logEntries.isNotEmpty()) {
            append("BREADCRUMBS\n===========\n\n")
            append(logEntries.joinToString("\n"))
            append("\n\n")
        }

        append("FINAL CRASH\n===========\n\n")
        append(e.stackTraceToString())
    }

    data class LogEntry(val severity: Severity, val message: String, val tag: String, val throwable: Throwable?) {
        override fun toString(): String = buildString {
            append("$severity - $tag - $message")
            throwable?.let<Throwable, Unit> {
                append("\n")
                append(it.getStackTrace().joinToString("\n"))
            }
        }
    }

    class CrashReportUploadException(val error: NSError): Exception("Crash report upload failed: ${error.localizedDescription}")
}
