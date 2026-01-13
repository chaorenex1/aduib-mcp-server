"""RPC 客户端基础设施 - 超时与重试"""
import asyncio
import functools
import logging
from typing import TypeVar, Callable, Optional

logger = logging.getLogger(__name__)
T = TypeVar('T')


class RPCConfig:
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0


class RPCTimeoutError(Exception):
    pass


class RPCError(Exception):
    pass


def with_timeout_and_retry(
    timeout: float = RPCConfig.DEFAULT_TIMEOUT,
    max_retries: int = RPCConfig.MAX_RETRIES,
    retry_delay: float = RPCConfig.RETRY_DELAY,
    retry_on: Optional[tuple] = None,
):
    if retry_on is None:
        retry_on = (asyncio.TimeoutError, ConnectionError, OSError)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except asyncio.TimeoutError:
                    last_error = RPCTimeoutError(f"RPC {func.__name__} timed out after {timeout}s")
                    logger.warning(f"RPC timeout (attempt {attempt + 1}): {func.__name__}")
                except retry_on as e:
                    last_error = RPCError(f"RPC {func.__name__} failed: {e}")
                    logger.warning(f"RPC error (attempt {attempt + 1}): {func.__name__}: {e}")
                except Exception:
                    raise
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (attempt + 1))
            raise last_error

        return wrapper

    return decorator


def with_timeout(timeout: float = RPCConfig.DEFAULT_TIMEOUT):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                raise RPCTimeoutError(f"RPC {func.__name__} timed out after {timeout}s")

        return wrapper

    return decorator
