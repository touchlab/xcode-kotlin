# Before running this, add LLDB to your PYTHONPATH (e.g. PYTHONPATH=`lldb -P`)

import os
import subprocess

from lldb import SBDebugger, SBTarget, LLDB_ARCH_DEFAULT, SBEvent, SBListener, SBProcess, eStateStopped

gradle_invoke = subprocess.Popen(['./gradlew', 'linkDebugExecutableMacosArm64'], cwd='test_project')
gradle_invoke.wait()

exe = 'test_project/build/bin/macosArm64/debugExecutable/test_project.kexe'

# Initialize the debugger before making any API calls.
SBDebugger.Initialize()
# Create a new debugger instance in your module if your module
# can be run from the command line. When we run a script from
# the command line, we won't have any debugger object in
# lldb.debugger, so we can just create it if it will be needed
debugger: SBDebugger = SBDebugger.Create()

# When we step or continue, don't return from the function until the process
# stops. Otherwise we would have to handle the process events ourselves which, while doable is
# a little tricky.  We do this by setting the async mode to false.
debugger.SetAsync(False)

# Import our module
debugger.HandleCommand('command script import touchlab_kotlin_lldb')

target: SBTarget = debugger.CreateTargetWithFileAndArch(exe, LLDB_ARCH_DEFAULT)

if target:
    target.BreakpointCreateByLocation('main.kt', 13)

    process = target.LaunchSimple(None, None, os.getcwd())

    if process:
        debugger.HandleCommand('fr v --ptr-depth 16')
        # debugger.HandleCommand('fr v --ptr-depth 16 -- data')

        process.Kill()

# Finally, dispose of the debugger you just made.
SBDebugger.Destroy(debugger)
# Terminate the debug session
SBDebugger.Terminate()
