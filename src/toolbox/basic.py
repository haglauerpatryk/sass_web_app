import threading, os, inspect

from functools import wraps
from django.conf import settings

from toolbox.ping_manager import PingManager
from toolbox.response_objects import LogManager
from toolbox.toolbox_manager import ToolBoxManager

class ToolBox(PingManager):
    _storage = threading.local()

    @property
    def log_manager(self):
        if not hasattr(self._storage, 'log_manager'):
            self._storage.log_manager = LogManager()
        return self._storage.log_manager

    
    def catch_error(self, handlers: dict):
        def decorator(func):
            wrapped_with_pings = self.get_ping_decorator()(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return wrapped_with_pings(*args, **kwargs)
                except Exception as e:
                    context = {
                        "func": func,
                        "args": args,
                        "kwargs": kwargs,
                        "request": next((a for a in args if hasattr(a, "user")), None),
                        "toolbox": self,
                    }

                    func_name = func.__name__
                    func_path = os.path.relpath(
                        inspect.getfile(func), settings.BASE_DIR
                    )
                    err_msg = f"TRIGGER: {type(e).__name__}: {e}"

                    self.log_manager.add_error_log(
                        err_msg,
                        func_name=func_name,
                        func_path=func_path,
                    )

                    for exc_type, handler in handlers.items():
                        if isinstance(e, exc_type):
                            return handler(e, context)

                    if Exception in handlers:
                        return handlers[Exception](e, context)

                    raise

            return wrapper
        return decorator