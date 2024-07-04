import re

from lldb import SBDebugger, SBExecutionContext, SBCommandReturnObject


class SymbolByNameCommand:
    program = 'symbol_by_name'

    def __init__(self, debugger, unused):
        pass

    def __call__(
            self,
            debugger: SBDebugger,
            command,
            exe_ctx: SBExecutionContext,
            result: SBCommandReturnObject,
    ):
        target = debugger.GetSelectedTarget()
        process = target.GetProcess()
        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame()
        tokens = command.split()
        mask = re.compile(tokens[0])
        symbols = list(filter(lambda v: mask.match(v.name), frame.GetModule().symbols))
        visited = list()
        for symbol in symbols:
            name = symbol.name
            if name in visited:
                continue
            visited.append(name)
            result.AppendMessage("{}: {:#x}".format(name, symbol.GetStartAddress().GetLoadAddress(target)))
