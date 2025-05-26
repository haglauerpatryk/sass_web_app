from functools import wraps
from toolbox.response_objects import LogManager
from toolbox.toolbox_manager import ToolBoxManager
from toolbox.ping_manager import PingManager
from django.conf import settings

import threading
import inspect

class ToolBox(PingManager, ErrorManager):
    _storage = threading.local()

    @property
    def log_manager(self):
        if not hasattr(self._storage, 'log_manager'):
            self._storage.log_manager = LogManager()
        return self._storage.log_manager


    def __init__(self):
        self.decorators = []
        self.state = {}


    def _create_feature_decorator(self, pre_logic=None, post_logic=None):
        """
        Generic method to create a decorator for a feature.

        :param feature_name: Name of the feature to apply.
        :param pre_logic: Callable for pre-execution logic (optional).
        :param post_logic: Callable for post-execution logic (optional).
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if pre_logic:
                    pre_logic(self, *args, **kwargs)

                result = func(*args, **kwargs)

                if post_logic:
                    post_logic(self, result, *args, **kwargs)

                return result
            return wrapper

        self.decorators.append(decorator)
        return self


    def func_with_args(self):
        """
        Example feature to log input arguments.
        """
        return self._create_feature_decorator(
            pre_logic=lambda toolbox, args, kwargs: toolbox.log_manager.add_info_log(
                f"Arguments for the function: args={args}, kwargs={kwargs}"
            ),
            post_logic=lambda toolbox, result, args, kwargs: toolbox.log_manager.add_info_log(
                f"Function result: {result}"
            ),
        )


    def track_time(self):
        from time import perf_counter
        return self._create_feature_decorator(
            pre_logic=lambda toolbox, *args, **kwargs: setattr(toolbox, "_start_time", perf_counter()),
            post_logic=lambda toolbox, result, *args, **kwargs: toolbox.log_manager.add_info_log(
                message = "seconds.",
                func_ping = f"track_time: Function executed in {perf_counter() - getattr(toolbox, '_start_time', 0)} seconds"
            ),
        )


    def func_a(self):
        return self._create_feature_decorator(
            pre_logic=lambda toolbox, *args, **kwargs: toolbox.log_manager.add_info_log("func_a() is decorating the function"),
            post_logic=lambda toolbox, result, *args, **kwargs: toolbox.log_manager.add_info_log("func_a() post-processing"),
        )


    def ping(self):
        return self._create_feature_decorator(
            pre_logic=lambda toolbox, *args, **kwargs: toolbox.log_manager.add_info_log(
                func_ping = toolbox.state.get("func_ping")
            ),
        )


    def __call__(self, func):
        if ToolBoxManager.DEBUG:
            if ToolBoxManager.PING:
                self.state["func_ping"] = self.get_ping(func)

        for decorator in reversed(self.decorators):
            func = decorator(func)

        def final_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            self.log_manager.display_logs()
            return result

        return final_wrapper


