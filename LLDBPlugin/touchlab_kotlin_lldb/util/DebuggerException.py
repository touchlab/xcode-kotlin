class DebuggerException(Exception):
    def __init__(self, msg: str):
        self.msg: str = msg
