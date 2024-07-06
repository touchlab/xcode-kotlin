from typing import Optional

from .log import log
from .kotlin_object_to_cstring import kotlin_object_to_string
from .DebuggerException import DebuggerException
from .expression import evaluate

NULL = 'null'


def strip_quotes(name: Optional[str]):
    return "" if (name is None) else name.strip('"')
