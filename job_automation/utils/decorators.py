"""
Decorators for job automation.
"""

import functools
import time
from typing import Callable, Any, Optional, Dict
from datetime import datetime

from ..core.job import Job, JobPriority
from ..core.logger import Logger


def job_task(name: Optional[str] = None, 
             priority: JobPriority = JobPriority.NORMAL,
             timeout: Optional[int] = None,
             max_retries: int = 3,
             tags: Optional[list] = None,
             metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to mark a function as a job task.
    
    Args:
        name: Job name (defaults to function name)
        priority: Job priority
        timeout: Job timeout in seconds
        max_retries: Maximum retry attempts
        tags: Job tags
        metadata: Job metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the function
            return func(*args, **kwargs)
        
        # Add job metadata to the function
        wrapper._job_config = {
            'name': name or func.__name__,
            'priority': priority,
            'timeout': timeout,
            'max_retries': max_retries,
            'tags': tags or [],
            'metadata': metadata or {}
        }
        
        return wrapper
    
    return decorator


def retry_on_failure(max_retries: int = 3, 
                    delay: float = 1.0,
                    backoff: float = 2.0,
                    exceptions: tuple = (Exception,),
                    logger: Optional[Logger] = None):
    """
    Decorator to retry function execution on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
        logger: Logger instance
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or Logger()
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        _logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    _logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                                  f"retrying in {wait_time:.2f} seconds: {e}")
                    time.sleep(wait_time)
            
            return None
        
        return wrapper
    
    return decorator


def timing_decorator(logger: Optional[Logger] = None):
    """
    Decorator to time function execution.
    
    Args:
        logger: Logger instance
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or Logger()
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                _logger.info(f"Function {func.__name__} completed in {execution_time:.3f} seconds")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                _logger.error(f"Function {func.__name__} failed after {execution_time:.3f} seconds: {e}")
                raise
        
        return wrapper
    
    return decorator


def log_execution(logger: Optional[Logger] = None, 
                 log_args: bool = False,
                 log_result: bool = False):
    """
    Decorator to log function execution.
    
    Args:
        logger: Logger instance
        log_args: Whether to log function arguments
        log_result: Whether to log function result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or Logger()
            
            # Log function start
            log_msg = f"Starting execution of {func.__name__}"
            if log_args:
                log_msg += f" with args={args}, kwargs={kwargs}"
            _logger.info(log_msg)
            
            try:
                result = func(*args, **kwargs)
                
                # Log function completion
                log_msg = f"Completed execution of {func.__name__}"
                if log_result:
                    log_msg += f" with result={result}"
                _logger.info(log_msg)
                
                return result
                
            except Exception as e:
                _logger.error(f"Execution of {func.__name__} failed: {e}")
                raise
        
        return wrapper
    
    return decorator


def rate_limit(calls_per_second: float = 1.0):
    """
    Decorator to rate limit function calls.
    
    Args:
        calls_per_second: Maximum calls per second
    """
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        return wrapper
    
    return decorator


def cache_result(ttl: int = 300):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            
            return result
        
        return wrapper
    
    return decorator