from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp

from ..exceptions import APIError, InvalidURLError, NetworkError, SerializationError, TimeoutError
from .retry import retry_with_backoff


class TransportClient:
    """Async HTTP transport for MAX API."""

    def __init__(
        self,
        token: str,
        base_url: str,
        version: str,
        timeout_seconds: int,
        max_retries: int,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            raise InvalidURLError("invalid API URL")

        self._token = token
        self._base_url = base_url.rstrip("/") + "/"
        self._version = version
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

        self._session = session
        self._owns_session = session is None
        self._error_queue: "asyncio.Queue[Exception]" = asyncio.Queue()

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def version(self) -> str:
        return self._version

    async def __aenter__(self) -> "TransportClient":
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def open(self) -> None:
        if self._session is not None:
            return
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self._owns_session = True

    async def close(self) -> None:
        if self._session is None:
            return
        if self._owns_session:
            await self._session.close()
        self._session = None

    def errors(self) -> "asyncio.Queue[Exception]":
        return self._error_queue

    async def notify_error(self, error: Exception) -> None:
        if error is None:
            return
        await self._error_queue.put(error)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            await self.open()
        if self._session is None:
            raise RuntimeError("session is not initialized")
        return self._session

    async def get_session(self) -> aiohttp.ClientSession:
        return await self._ensure_session()

    async def request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        authorized: bool = True,
        expected_statuses: Tuple[int, ...] = (200,),
        retry_attempts: int = 1,
        retry_predicate: Optional[Callable[[Exception], bool]] = None,
    ) -> Dict[str, Any]:
        operation = "{0} {1}".format(method, path)
        query = self._normalize_params(params)
        query["v"] = self._version

        headers = {
            "User-Agent": "maxpybot/{0}".format(self._version),
        }
        if authorized:
            headers["Authorization"] = self._token

        if json_body is not None:
            try:
                json.dumps(json_body)
            except Exception as exc:  # noqa: BLE001
                raise SerializationError("marshal", "request body", exc)

        if retry_attempts < 1:
            retry_attempts = 1
        if retry_predicate is None:
            retry_predicate = _default_retry_predicate

        async def _single_request() -> Dict[str, Any]:
            session = await self._ensure_session()
            url = urljoin(self._base_url, path.lstrip("/"))
            try:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    params=query,
                    json=json_body,
                    headers=headers,
                ) as response:
                    body_text = await response.text()
                    if response.status not in expected_statuses:
                        self._raise_api_error(response.status, body_text)
                    if body_text.strip() == "":
                        return {}
                    try:
                        decoded = json.loads(body_text)
                    except Exception as exc:  # noqa: BLE001
                        raise SerializationError("unmarshal", "response body", exc)
                    if not isinstance(decoded, dict):
                        return {"result": decoded}
                    return decoded
            except TimeoutError:
                raise
            except asyncio.TimeoutError:
                raise TimeoutError(operation, "request timeout exceeded")
            except aiohttp.ClientError as exc:
                raise NetworkError(operation, exc)

        if retry_attempts == 1:
            return await _single_request()

        try:
            return await retry_with_backoff(
                coro_factory=_single_request,
                should_retry=retry_predicate,
                attempts=retry_attempts,
                initial_delay_seconds=1.0,
            )
        except Exception as exc:  # noqa: BLE001
            await self.notify_error(exc)
            raise

    @staticmethod
    def _normalize_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not params:
            return {}
        result: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                result[key] = "true" if value else "false"
            elif isinstance(value, (list, tuple, set)):
                result[key] = list(value)
            else:
                result[key] = str(value)
        return result

    @staticmethod
    def _raise_api_error(status_code: int, body_text: str) -> None:
        code = ""
        message = ""
        if body_text:
            try:
                parsed = json.loads(body_text)
            except Exception:  # noqa: BLE001
                parsed = None
            if isinstance(parsed, dict):
                code = str(parsed.get("code") or "")
                message = str(parsed.get("message") or "")

        if not code:
            code = "http_{0}".format(status_code)
        raise APIError(status_code, code, message or None)


def _default_retry_predicate(error: Exception) -> bool:
    return isinstance(error, (TimeoutError, NetworkError))
