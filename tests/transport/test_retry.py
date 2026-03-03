import asyncio
import pytest
from maxpybot.transport.retry import retry_with_backoff

@pytest.mark.asyncio
async def test_retry_success_first_attempt() -> None:
    calls = 0
    async def coro():
        nonlocal calls
        calls += 1
        return "ok"
    
    result = await retry_with_backoff(coro, lambda e: True, attempts=3)
    assert result == "ok"
    assert calls == 1

@pytest.mark.asyncio
async def test_retry_success_after_failure() -> None:
    calls = 0
    async def coro():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("fail")
        return "ok"
    
    # Use small initial delay instead of mocking to avoid recursion issues
    result = await retry_with_backoff(
        coro, 
        lambda e: isinstance(e, ValueError), 
        attempts=3,
        initial_delay_seconds=0.01
    )
    assert result == "ok"
    assert calls == 2

@pytest.mark.asyncio
async def test_retry_exhausted_attempts() -> None:
    calls = 0
    async def coro():
        nonlocal calls
        calls += 1
        raise ValueError("permanent fail")
    
    with pytest.raises(ValueError, match="permanent fail"):
        await retry_with_backoff(
            coro, 
            lambda e: True, 
            attempts=2,
            initial_delay_seconds=0.01
        )
    assert calls == 2

@pytest.mark.asyncio
async def test_retry_no_retry_on_specific_error() -> None:
    calls = 0
    async def coro():
        nonlocal calls
        calls += 1
        raise RuntimeError("no retry")
    
    def should_retry(exc):
        return not isinstance(exc, RuntimeError)

    with pytest.raises(RuntimeError, match="no retry"):
        await retry_with_backoff(coro, should_retry, attempts=3)
    assert calls == 1
