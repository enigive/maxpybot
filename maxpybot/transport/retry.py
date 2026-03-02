from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


async def retry_with_backoff(
    coro_factory: Callable[[], Awaitable[T]],
    should_retry: Callable[[Exception], bool],
    attempts: int,
    initial_delay_seconds: float = 1.0,
) -> T:
    """Retry coroutine with exponential backoff."""

    last_error = None
    delay = initial_delay_seconds
    for attempt in range(attempts):
        try:
            return await coro_factory()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= attempts - 1 or not should_retry(exc):
                raise
            await asyncio.sleep(delay)
            delay *= 2
    if last_error is not None:
        raise last_error
    raise RuntimeError("unreachable retry state")
