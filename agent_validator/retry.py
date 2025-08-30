"""Retry logic with exponential backoff and jitter."""

import random
import time
from typing import Any, Callable, Optional

from .typing_ import RetryFunction


def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    factor: float = 2.0,
    timeout_s: Optional[float] = None,
) -> Any:
    """
    Retry a function with exponential backoff and jitter.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        factor: Exponential factor
        timeout_s: Total timeout in seconds (None for no timeout)
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: Last exception raised by the function
    """
    start_time = time.time()
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # Check timeout
            if timeout_s and (time.time() - start_time) > timeout_s:
                raise TimeoutError(f"Operation timed out after {timeout_s}s")

            return func()

        except Exception as e:
            last_exception = e

            # Don't retry on the last attempt
            if attempt == max_retries:
                break

            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (factor ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)  # 10% jitter
            total_delay = delay + jitter

            # Check if we would exceed timeout
            if timeout_s and (time.time() - start_time + total_delay) > timeout_s:
                break

            time.sleep(total_delay)

    raise last_exception


def create_retry_function(
    original_fn: RetryFunction,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    factor: float = 2.0,
    timeout_s: Optional[float] = None,
) -> RetryFunction:
    """
    Create a retry function that wraps the original function.
    
    Args:
        original_fn: Original function to wrap
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        factor: Exponential factor
        timeout_s: Total timeout in seconds
        
    Returns:
        Wrapped function with retry logic
    """
    def retry_wrapper(prompt: str, context: dict) -> Any:
        def attempt():
            return original_fn(prompt, context)

        return retry_with_backoff(
            attempt,
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            factor=factor,
            timeout_s=timeout_s,
        )

    return retry_wrapper
