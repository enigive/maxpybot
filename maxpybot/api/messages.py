from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from ..exceptions import APIError
from ..types import CallbackAnswerSchema, NewMessageSchema, build_request_payload
from .base import BaseAPIGroup


class MessagesAPI(BaseAPIGroup):
    async def get_messages(
        self,
        chat_id: Optional[int] = None,
        message_ids: Optional[List[str]] = None,
        from_marker: Optional[int] = None,
        to_marker: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Any:
        params: Dict[str, Any] = {}
        if chat_id is not None:
            params["chat_id"] = chat_id
        if message_ids:
            params["message_ids"] = ",".join(message_ids)
        if from_marker is not None:
            params["from"] = from_marker
        if to_marker is not None:
            params["to"] = to_marker
        if count is not None:
            params["count"] = count
        return await self._request_model("MessageList", "GET", "messages", params=params)

    async def send_message(
        self,
        body: Union[Dict[str, Any], NewMessageSchema],
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Any:
        params: Dict[str, Any] = {}
        if chat_id is not None:
            params["chat_id"] = chat_id
        if user_id is not None:
            params["user_id"] = user_id

        payload = build_request_payload(body, NewMessageSchema)

        async def _call() -> Any:
            return await self._request_model(
                "SendMessageResult",
                "POST",
                "messages",
                params=params,
                json_body=payload,
            )

        return await self._retry_attachment_not_ready(_call)

    async def edit_message(self, message_id: str, body: Union[Dict[str, Any], NewMessageSchema]) -> Any:
        params = {"message_id": message_id}
        payload = build_request_payload(body, NewMessageSchema)

        async def _call() -> Any:
            return await self._request_model(
                "SimpleQueryResult",
                "PUT",
                "messages",
                params=params,
                json_body=payload,
            )

        return await self._retry_attachment_not_ready(_call)

    async def delete_message(self, message_id: str) -> Any:
        return await self._request_model("SimpleQueryResult", "DELETE", "messages", params={"message_id": message_id})

    async def get_message_by_id(self, message_id: str) -> Any:
        return await self._request_model("Message", "GET", "messages/{0}".format(quote(message_id, safe="_-")))

    async def get_video_attachment_details(self, video_token: str) -> Any:
        return await self._request_model(
            "VideoAttachmentDetails",
            "GET",
            "videos/{0}".format(quote(video_token, safe="_-")),
        )

    async def answer_on_callback(
        self,
        callback_id: str,
        callback: Union[Dict[str, Any], CallbackAnswerSchema],
    ) -> Any:
        body = build_request_payload(callback, CallbackAnswerSchema)
        return await self._request_model(
            "SimpleQueryResult",
            "POST",
            "answers",
            params={"callback_id": callback_id},
            json_body=body,
        )

    async def _retry_attachment_not_ready(self, callback: Any) -> Any:
        retries = getattr(self._transport, "max_retries", 3)
        for attempt in range(retries):
            try:
                return await callback()
            except APIError as exc:
                if not exc.is_attachment_not_ready() or attempt >= retries - 1:
                    raise
                await asyncio.sleep(float(2 ** attempt))
        raise RuntimeError("unreachable retries state")

    # OpenAPI parity aliases (operationId)
    getMessages = get_messages
    sendMessage = send_message
    editMessage = edit_message
    deleteMessage = delete_message
    getMessageById = get_message_by_id
    getVideoAttachmentDetails = get_video_attachment_details
    answerOnCallback = answer_on_callback
