package co.touchlab.xcode.cli.util

import co.touchlab.kermit.Logger
import kotlinx.cinterop.ExperimentalForeignApi
import platform.posix.fflush
import platform.posix.fprintf
import platform.posix.stderr

object Console {
    private val logger = Logger.withTag("Console")

    fun echo(text: String = "") {
        logger.v { text }
        println(text)
    }

    fun confirm(text: String): Boolean {
        while (true) {
            val input = prompt(text, newLine = false)?.trim()?.lowercase() ?: return false
            return when (input) {
                "y", "yes" -> true
                "n", "no" -> false
                else -> {
                    printError("Invalid input '$input', try again.")
                    continue
                }
            }
        }
    }

    fun prompt(text: String, newLine: Boolean = false): String? {
        if (newLine) {
            println(text)
        } else {
            print(text)
        }
        return readLine()
    }

    @OptIn(ExperimentalForeignApi::class)
    fun printError(message: String) {
        fprintf(stderr, message)
        fflush(stderr)
    }
}
