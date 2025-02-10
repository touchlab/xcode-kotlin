package co.touchlab.xcode.cli.util

import com.github.ajalt.mordant.terminal.TerminalRecorder
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.runBlocking
import platform.Foundation.NSError
import platform.Foundation.NSMutableURLRequest
import platform.Foundation.NSURL
import platform.Foundation.NSURLSession
import platform.Foundation.NSURLSessionConfiguration.Companion.defaultSessionConfiguration
import platform.Foundation.NSUTF8StringEncoding
import platform.Foundation.dataTaskWithRequest
import platform.Foundation.dataUsingEncoding
import platform.Foundation.setHTTPBody
import platform.Foundation.setHTTPMethod
import platform.Foundation.setValue

class CrashHelper {
    fun upload(e: Throwable, recorder: TerminalRecorder) {
        upload(capture(e, recorder.output()))
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

    private fun capture(e: Throwable, recorderOutput: String): String = buildString {
        if (recorderOutput.isNotBlank()) {
            append("BREADCRUMBS\n===========\n\n")
            append(recorderOutput)
            append("\n\n")
        }

        append("FINAL CRASH\n===========\n\n")
        append(e.stackTraceToString())
    }

    class CrashReportUploadException(val error: NSError): Exception("Crash report upload failed: ${error.localizedDescription}")
}
