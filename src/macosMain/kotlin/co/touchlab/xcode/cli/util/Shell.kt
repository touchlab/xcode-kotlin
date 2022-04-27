package co.touchlab.xcode.cli.util

import co.touchlab.kermit.Logger
import platform.Foundation.NSData
import platform.Foundation.NSMutableData
import platform.Foundation.NSPipe
import platform.Foundation.NSString
import platform.Foundation.NSTask
import platform.Foundation.NSTaskTerminationReason
import platform.Foundation.NSUTF8StringEncoding
import platform.Foundation.appendData
import platform.Foundation.closeFile
import platform.Foundation.create
import platform.Foundation.launch
import platform.Foundation.launchPath
import platform.Foundation.readabilityHandler
import platform.Foundation.writeData
import platform.Foundation.writeabilityHandler
import platform.darwin.DISPATCH_TIME_FOREVER
import platform.darwin.dispatch_semaphore_create
import platform.darwin.dispatch_semaphore_signal
import platform.darwin.dispatch_semaphore_wait
import platform.posix.EXIT_SUCCESS
import kotlin.contracts.contract

object Shell {
    private val logger = Logger.withTag("Shell")
    fun exec(launchPath: String, vararg arguments: String, input: NSData? = null): ExecutionResult {
        return exec(launchPath, arguments.toList(), input)
    }

    fun exec(launchPath: String, arguments: List<String>, input: NSData? = null): ExecutionResult {
        return exec(Task(launchPath, arguments, input))
    }

    fun exec(task: Task): ExecutionResult {
        val waitHandle = dispatch_semaphore_create(0)
        val nsTask = NSTask()
        nsTask.launchPath = task.launchPath
        nsTask.arguments = task.arguments

        val inputFile = if (task.input != null) {
            val inputPipe = NSPipe()
            val inputFile = inputPipe.fileHandleForWriting
            nsTask.standardInput = inputPipe
            inputFile.writeabilityHandler = {
                inputFile.writeData(task.input)
                inputFile.closeFile()
                inputFile.writeabilityHandler = null
            }
            inputFile
        } else {
            null
        }

        val taskOutput = NSMutableData()
        val outputPipe = NSPipe()
        val outputFile = outputPipe.fileHandleForReading
        nsTask.standardOutput = outputPipe
        outputFile.readabilityHandler = {
            taskOutput.appendData(outputFile.availableData)
        }

        val taskError = NSMutableData()
        val errorPipe = NSPipe()
        val errorFile = errorPipe.fileHandleForReading
        nsTask.standardError = errorPipe
        errorFile.readabilityHandler = {
            taskError.appendData(errorFile.availableData)
        }

        nsTask.terminationHandler = {
            inputFile?.writeabilityHandler = null
            outputFile.readabilityHandler = null
            errorFile.readabilityHandler = null
            dispatch_semaphore_signal(waitHandle)
        }

        nsTask.launch()

        dispatch_semaphore_wait(waitHandle, DISPATCH_TIME_FOREVER)

        return ExecutionResult(
            task = task,
            outputData = taskOutput,
            output = NSString.create(taskOutput, NSUTF8StringEncoding) as String?,
            errorData = taskError,
            error = NSString.create(taskError, NSUTF8StringEncoding) as String?,
            status = nsTask.terminationStatus,
            reason = nsTask.terminationReason,
        ).also {
            if (!it.error.isNullOrBlank()) {
                logger.w {
                    "Task $nsTask had non-empty error output:\n\n${it.error}\n"
                }
            }
        }
    }

    class Task(
        val launchPath: String,
        val arguments: List<String>,
        val input: NSData?
    ) {
        override fun toString(): String {
            return "$launchPath ${arguments.joinToString(" ")} (input: ${input?.length ?: 0} bytes)"
        }
    }

    class ExecutionResult(
        val task: Task,
        val outputData: NSData,
        val output: String?,
        val errorData: NSData,
        val error: String?,
        val status: Int,
        val reason: NSTaskTerminationReason,
    ) {
        val success: Boolean
            get() = status == EXIT_SUCCESS

        fun checkSuccessful(lazyMessage: () -> String): ExecutionResult {
            check(success) {
                """
                    |${lazyMessage}. Task $task exited with code $status (reason $reason).
                    |
                    |Standard input:
                    ${task.input?.let { NSString.create(data = it, encoding = NSUTF8StringEncoding) }?.kt?.lines()?.joinToString("\n") { "|\t$it" } ?: ""}
                    |
                    |Standard output:
                    ${output?.lines()?.joinToString("\n") { "|\t$it" } ?: ""}
                    |
                    |Standard error:
                    ${error?.lines()?.joinToString("\n") { "|\t$it" } ?: ""}
                """.trimMargin()
            }
            return this
        }
    }
}