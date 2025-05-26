from functools import wraps
from typing import Callable, Any

def my_decorator(func: Callable) -> Callable:
    """
    A blank decorator template to wrap a function with additional behavior.

    Parameters:
        func (Callable): The function to be wrapped by the decorator.

    Returns:
        Callable: The wrapped function with additional behavior.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Pre-function logic (optional)
        print(f"Before calling {func.__name__}")

        # Call the original function
        result = func(*args, **kwargs)

        # Post-function logic (optional)
        print(f"After calling {func.__name__}")

        return result

    return wrapper