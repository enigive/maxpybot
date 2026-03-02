import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from maxpybot.exceptions import APIError, NetworkError, SerializationError, TimeoutError
from maxpybot.transport.client import TransportClient

ME_URL = "https://platform-api.max.ru/me?v=1.2.5"


@pytest.mark.asyncio
async def test_request_json_success() -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with aioresponses() as mocked:
            mocked.get(ME_URL, payload={"user_id": 100})
            response = await client.request_json("GET", "me")
            assert response["user_id"] == 100
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403, 404, 429, 500])
async def test_request_json_http_errors(status_code: int) -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with aioresponses() as mocked:
            mocked.get(ME_URL, status=status_code, payload={"code": "some.error", "message": "details"})
            with pytest.raises(APIError) as error:
                await client.request_json("GET", "me")
            assert error.value.status_code == status_code
            assert error.value.message == "some.error"
            assert error.value.details == "details"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_json_timeout_error() -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with aioresponses() as mocked:
            mocked.get(ME_URL, exception=asyncio.TimeoutError())
            with pytest.raises(TimeoutError):
                await client.request_json("GET", "me")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_json_network_error() -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with aioresponses() as mocked:
            mocked.get(ME_URL, exception=aiohttp.ClientConnectionError())
            with pytest.raises(NetworkError):
                await client.request_json("GET", "me")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_json_invalid_json_response() -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with aioresponses() as mocked:
            mocked.get(ME_URL, status=200, body="not-json")
            with pytest.raises(SerializationError):
                await client.request_json("GET", "me")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_json_invalid_request_body_serialization() -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with pytest.raises(SerializationError):
            await client.request_json("POST", "messages", json_body={"invalid": {1, 2}})
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_json_retries_on_timeout() -> None:
    client = TransportClient(
        token="token",
        base_url="https://platform-api.max.ru/",
        version="1.2.5",
        timeout_seconds=30,
        max_retries=3,
    )
    try:
        with aioresponses() as mocked:
            mocked.get(ME_URL, exception=asyncio.TimeoutError())
            mocked.get(ME_URL, payload={"ok": True})
            response = await client.request_json("GET", "me", retry_attempts=2)
            assert response["ok"] is True
    finally:
        await client.close()
