from typing import Optional

from lldb import SBDebugger, SBExecutionContext, SBCommandReturnObject, SBTarget, SBSymbol, SBInstructionList
from touchlab_kotlin_lldb.util import evaluate, DebuggerException

import re


class GCCollectCommand:
    program = 'force_gc'

    def __init__(self, debugger, unused):
        pass

    def __call__(self, debugger: SBDebugger, command, exe_ctx: SBExecutionContext, result: SBCommandReturnObject):
        try:
            target = debugger.GetSelectedTarget()
            schedule_gc_function = self._find_single_function_symbol('kotlin::gcScheduler::GCScheduler::scheduleAndWaitFinalized()', target, result)
            deinit_memory_function = self._find_single_function_symbol('DeinitMemory', target, result)
            global_data_symbol = self._find_single_symbol("(anonymous namespace)::globalDataInstance", target, result)

            gc_scheduler_offset = self._find_gc_scheduler_offset(deinit_memory_function, schedule_gc_function, target)

            schedule_gc_function_addr = schedule_gc_function.addr.GetLoadAddress(target)
            global_data_addr = global_data_symbol.addr.GetLoadAddress(target)
            gc_scheduler_addr = global_data_addr + gc_scheduler_offset

            evaluate(
                '((void (*)(void*)){:#x})((void*){:#x})',
                schedule_gc_function_addr,
                gc_scheduler_addr
            )
            evaluate(
                '((void (*)(void*)){:#x})((void*){:#x})',
                schedule_gc_function_addr,
                gc_scheduler_addr
            )

        except DebuggerException as e:
            result.SetError("{} Please report this to the xcode-kotlin GitHub.".format(e.msg))
            return


    @staticmethod
    def _find_single_function_symbol(symbol_name: str, target: SBTarget, result: SBCommandReturnObject) -> SBSymbol:
        functions = target.FindFunctions(symbol_name)
        if functions.GetSize() >= 1:
            if not functions.GetSize() == 1:
                result.AppendWarning("Multiple ({}) symbols found for function {}".format(functions.GetSize(), symbol_name))
            return functions[0].GetSymbol()
        else:
            raise DebuggerException("Could not find symbol for function {}.".format(symbol_name))

    @staticmethod
    def _find_single_symbol(symbol_name: str, target: SBTarget, result: SBCommandReturnObject) -> SBSymbol:
        symbols = target.FindSymbols(symbol_name)
        if symbols.GetSize() >= 1:
            if not symbols.GetSize() == 1:
                result.AppendWarning(
                    "Multiple ({}) symbols found for function {}".format(symbols.GetSize(), symbol_name))
            return symbols[0].GetSymbol()
        else:
            raise DebuggerException("Could not find symbol for function {}.".format(symbol_name))

    @staticmethod
    def _find_gc_scheduler_offset(deinit_memory: SBSymbol, schedule_gc: SBSymbol, target: SBTarget) -> int:
        instructions = deinit_memory.GetInstructions(target)
        load_addr = "{:#x}".format(schedule_gc.addr.GetLoadAddress(target))

        previous_branch_instruction_index: int = 0
        schedule_gc_branch_instruction_index: Optional[int] = None
        for i in range(len(instructions)):
            instruction = instructions[i]
            if instruction.DoesBranch():
                if instruction.GetOperands(target) == load_addr:
                    schedule_gc_branch_instruction_index = i
                    break
                else:
                    previous_branch_instruction_index = i

        if not schedule_gc_branch_instruction_index:
            raise DebuggerException(
                "Could not find a branch instruction to {} inside {}.".format(
                    schedule_gc.GetDisplayName(), deinit_memory.GetDisplayName()))

        match_pattern = "\\(anonymous namespace\\)::globalDataInstance\\s+\\+\\s+(\\d+)"
        gc_scheduler_offset: Optional[int] = None
        for i in range(previous_branch_instruction_index, schedule_gc_branch_instruction_index):
            instruction = instructions[i]
            match = re.search(match_pattern, instruction.GetComment(target))
            if match:
                gc_scheduler_offset = int(match.group(1))
                break

        if not gc_scheduler_offset:
            raise DebuggerException("Could not find gc_scheduler offset for globalDataInstance.")

        return gc_scheduler_offset