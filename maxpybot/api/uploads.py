from __future__ import annotations

import json
import os
from typing import Any, BinaryIO, Dict, Optional
from urllib.parse import unquote, urlparse

import aiohttp

from ..exceptions import APIError, NetworkError, SerializationError
from ..types.generated.runtime import validate_with_model
from .base import BaseAPIGroup


class UploadsAPI(BaseAPIGroup):
    async def get_upload_url(self, upload_type: str) -> Any:
        return await self._request_model("UploadEndpoint", "POST", "uploads", params={"type": upload_type})

    async def upload_media_from_reader(
        self,
        upload_type: str,
        reader: BinaryIO,
        file_name: Optional[str] = None,
    ) -> Any:
        endpoint = await self.get_upload_url(upload_type)
        endpoint_dict = _as_dict(endpoint)
        upload_url = str(endpoint_dict.get("url", ""))
        if not upload_url:
            raise SerializationError("decode", "upload endpoint", ValueError("empty upload url"))

        if file_name is None:
            file_name = "file"
        else:
            file_name = os.path.basename(file_name) or "file"

        data = aiohttp.FormData()
        data.add_field("data", reader, filename=file_name)

        session = await self._transport.get_session()
        try:
            async with session.post(upload_url, data=data) as response:
                raw = await response.text()
                if response.status < 200 or response.status >= 300:
                    code = "http_{0}".format(response.status)
                    details = raw
                    try:
                        decoded = json.loads(raw)
                        if isinstance(decoded, dict):
                            code = str(decoded.get("code") or code)
                            details = str(decoded.get("message") or details)
                    except Exception:  # noqa: BLE001
                        pass
                    raise APIError(response.status, code, details)

                # audio/video may only return status + token from upload endpoint
                if upload_type in ("audio", "video"):
                    return validate_with_model("UploadedInfo", {"token": endpoint_dict.get("token")})

                if raw.strip() == "":
                    return {}
                try:
                    decoded_body = json.loads(raw)
                except Exception as exc:  # noqa: BLE001
                    raise SerializationError("decode", "upload response", exc)
                if not isinstance(decoded_body, dict):
                    return {"result": decoded_body}
                model_name = "PhotoTokens" if upload_type == "image" else "UploadedInfo"
                return validate_with_model(model_name, decoded_body)
        except APIError:
            raise
        except aiohttp.ClientError as exc:
            raise NetworkError("POST upload", exc)

    async def upload_media_from_file(self, upload_type: str, file_path: str) -> Any:
        with open(file_path, "rb") as file_obj:
            return await self.upload_media_from_reader(upload_type, file_obj, file_path)

    async def upload_media_from_url(self, upload_type: str, url: str) -> Any:
        session = await self._transport.get_session()
        try:
            async with session.get(url) as response:
                if response.status < 200 or response.status >= 300:
                    raise APIError(response.status, "http_{0}".format(response.status), await response.text())
                file_name = _filename_from_response(response, url)
                content = await response.read()
        except APIError:
            raise
        except aiohttp.ClientError as exc:
            raise NetworkError("GET upload source", exc)

        # Use in-memory bytes for single-shot upload.
        from io import BytesIO

        return await self.upload_media_from_reader(upload_type, BytesIO(content), file_name=file_name)

    # OpenAPI parity aliases (operationId)
    getUploadUrl = get_upload_url


def _filename_from_response(response: aiohttp.ClientResponse, source_url: str) -> str:
    disposition = response.headers.get("Content-Disposition")
    if disposition and "filename=" in disposition:
        candidate = disposition.split("filename=", 1)[1].strip().strip('"')
        if candidate:
            return unquote(candidate)

    parsed = urlparse(source_url)
    path_name = os.path.basename(parsed.path)
    return path_name or "file"


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True)
    return {}
