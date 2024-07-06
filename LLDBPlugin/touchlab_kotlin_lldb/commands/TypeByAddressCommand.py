import lldb

from ..util import log


class TypeByAddressCommand:
    program = 'type_by_address'

    def __init__(self, debugger, internal_dict):
        pass

    def __call__(
            self,
            debugger: lldb.SBDebugger,
            command,
            exe_ctx: lldb.SBExecutionContext,
            result: lldb.SBCommandReturnObject
    ):
        log(lambda: "type_by_address_command:{}".format(command))
        result.AppendMessage("DEBUG: {}".format(command))
        tokens = command.split()
        target = debugger.GetSelectedTarget()
        types = _type_info_by_address(tokens[0], debugger)
        result.AppendMessage("DEBUG: {}".format(types))
        for t in types:
            result.AppendMessage("{}: {:#x}".format(t.name, t.GetStartAddress().GetLoadAddress(target)))


def _type_info_by_address(address, debugger: lldb.SBDebugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    candidates = list(filter(lambda x: x.GetStartAddress().GetLoadAddress(target) == address, frame.module.symbols))
    return candidates
