package co.touchlab.xcode.cli.util

import platform.Foundation.NSData
import platform.Foundation.NSMutableData
import platform.Foundation.NSPipe
import platform.Foundation.NSString
import platform.Foundation.NSTask
import platform.Foundation.NSTaskTerminationReason
import platform.Foundation.NSUTF8StringEncoding
import platform.Foundation.appendData
import platform.Foundation.create
import platform.Foundation.launch
import platform.Foundation.launchPath
import platform.Foundation.readabilityHandler
import platform.darwin.DISPATCH_TIME_FOREVER
import platform.darwin.dispatch_semaphore_create
import platform.darwin.dispatch_semaphore_signal
import platform.darwin.dispatch_semaphore_wait
import platform.posix.EXIT_SUCCESS

object Shell {
    fun exec(launchPath: String, vararg arguments: String): ExecutionResult {
        return exec(launchPath, arguments.toList())
    }

    fun exec(launchPath: String, arguments: List<String>): ExecutionResult {
        val waitHandle = dispatch_semaphore_create(0)
        val outputPipe = NSPipe()
        val outputFile = outputPipe.fileHandleForReading
        val errorPipe = NSPipe()
        val errorFile = errorPipe.fileHandleForReading

        val taskOutput = NSMutableData()
        val taskError = NSMutableData()
        val task = NSTask()
        task.launchPath = launchPath
        task.arguments = arguments
        task.standardOutput = outputPipe
        task.standardError = errorPipe

        outputFile.readabilityHandler = {
            taskOutput.appendData(outputFile.availableData)
        }
        errorFile.readabilityHandler = {
            taskError.appendData(errorFile.availableData)
        }
        task.terminationHandler = {
            outputFile.readabilityHandler = null
            errorFile.readabilityHandler = null
            dispatch_semaphore_signal(waitHandle)
        }

        task.launch()

        dispatch_semaphore_wait(waitHandle, DISPATCH_TIME_FOREVER)

        return ExecutionResult(
            outputData = taskOutput,
            output = NSString.create(taskOutput, NSUTF8StringEncoding) as String?,
            errorData = taskError,
            error = NSString.create(taskError, NSUTF8StringEncoding) as String?,
            status = task.terminationStatus,
            reason = task.terminationReason,
        )
    }

    class ExecutionResult(
        val outputData: NSData,
        val output: String?,
        val errorData: NSData,
        val error: String?,
        val status: Int,
        val reason: NSTaskTerminationReason,
    ) {
        val success: Boolean
            get() = status == EXIT_SUCCESS
    }
}