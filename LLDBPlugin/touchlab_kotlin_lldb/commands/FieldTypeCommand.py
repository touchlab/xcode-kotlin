from lldb import SBDebugger, SBExecutionContext, SBCommandReturnObject

from ..types.proxy import KonanProxyTypeProvider
from ..types.base import get_runtime_type


class FieldTypeCommand:
    program = 'field_type'

    def __init__(self, debugger, unused):
        pass

    def __call__(
            self,
            debugger: SBDebugger,
            command,
            exe_ctx: SBExecutionContext,
            result: SBCommandReturnObject,
    ):
        """
        Returns runtime type of foo.bar.baz field in the form "(foo.bar.baz <TYPE_NAME>)".
        If requested field could not be traced, then "<NO_FIELD_FOUND>" plug is used for type name.
        """
        fields = command.split('.')

        variable = exe_ctx.GetFrame().FindVariable(fields[0])

        for field_name in fields[1:]:
            if variable is not None:
                provider = KonanProxyTypeProvider(variable, {})
                field_index = provider.get_child_index(field_name)
                variable = provider.get_child_at_index(field_index)
            else:
                break

        desc = "<NO_FIELD_FOUND>"

        if variable is not None:
            rt = get_runtime_type(variable)
            if len(rt) > 0:
                desc = rt

        result.write("{}".format(desc))
