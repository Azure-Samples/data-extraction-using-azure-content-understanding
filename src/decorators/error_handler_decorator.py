from azure.functions import HttpResponse
import asyncio
from functools import wraps
import inspect
from models import HTTPError


def error_handler(func):
    """Decorator to handle errors in HTTP functions.

    Args:
        func (callable): The function to decorate.

    Returns:
        callable: The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function to handle errors.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            HttpResponse: The HTTP response.
        """
        try:
            # check if the funciton is async
            if inspect.iscoroutinefunction(func):
                # async function
                # run async function in sync mode
                return asyncio.run(func(*args, **kwargs))
            else:
                # sync function
                return func(*args, **kwargs)
        except HTTPError as e:
            return HttpResponse(
                str(e),
                status_code=e.status_code
            )
        except Exception:
            raise
    return wrapper
