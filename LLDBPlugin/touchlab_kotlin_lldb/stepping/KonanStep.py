class KonanStep(object):
    def __init__(self, thread_plan):
        self.thread_plan = thread_plan
        self.step_thread_plan = self.queue_thread_plan()

        debugger = thread_plan.GetThread().GetProcess().GetTarget().GetDebugger()
        self.avoid_no_debug = debugger.GetInternalVariableValue('target.process.thread.step-in-avoid-nodebug',
                                                                debugger.GetInstanceName()).GetStringAtIndex(0)

    def explains_stop(self, event):
        return True

    def should_stop(self, event):
        frame = self.thread_plan.GetThread().GetFrameAtIndex(0)
        source_file = frame.GetLineEntry().GetFileSpec().GetFilename()

        if self.avoid_no_debug == 'true' and source_file in [None, '<compiler-generated>']:
            self.step_thread_plan = self.queue_thread_plan()
            return False

        self.thread_plan.SetPlanComplete(True)
        return True

    def should_step(self):
        return True

    def queue_thread_plan(self):
        address = self.thread_plan.GetThread().GetFrameAtIndex(0).GetPCAddress()
        line_entry = self.thread_plan.GetThread().GetFrameAtIndex(0).GetLineEntry()
        begin_address = line_entry.GetStartAddress().GetFileAddress()
        end_address = line_entry.GetEndAddress().GetFileAddress()
        return self.do_queue_thread_plan(address, end_address - begin_address)
