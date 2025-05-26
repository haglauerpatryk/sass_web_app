import os
import inspect
import logging

from django.conf import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    RetryError,
    before_sleep_log,
)

def reroute_with_retry(fallback_func, toolbox, retries=3, delay=0.2):
    func_name = fallback_func.__name__
    func_path = os.path.relpath(inspect.getfile(fallback_func), settings.BASE_DIR)


    def _before_sleep(retry_state):
        exc = retry_state.outcome.exception()
        toolbox.log_manager.add_error_log(
            f"RETRY {retry_state.attempt_number}: {func_name}\n"
            f"TRIGGER: {type(exc).__name__}: {exc}",
            func_name=func_name,
            func_path=func_path,
        )


    @retry(
        stop=stop_after_attempt(retries),
        wait=wait_fixed(delay),
        before_sleep=_before_sleep,
        reraise=True
    )
    def _call_with_retry(*args, **kwargs):
        return fallback_func(*args, **kwargs)


    def handler(error, context):
        """
        Tenacity will automatically retry `_call_with_retry`, logging on each wait.
        If all retries fail, the final exception is propagated.
        """
        args = context["args"]
        kwargs = context["kwargs"]
        try:
            return _call_with_retry(*args, **kwargs)
        except RetryError as re:
            # re.last_attempt.exception() is the underlying exception
            raise re.last_attempt.exception()

    return handler