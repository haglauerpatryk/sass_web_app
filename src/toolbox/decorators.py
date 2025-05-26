from functools import wraps

from toolbox.basic import ToolBox
from toolbox.toolbox_manager import ToolBoxManager

_light_tb = ToolBox()

def light_toolbox(func=None):
    decorator = (
        _light_tb.get_ping_decorator()
        if (ToolBoxManager.DEBUG and ToolBoxManager.PING)
        else (lambda f: f)
    )

    if func:
        return decorator(func)
    return decorator
