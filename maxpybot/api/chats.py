from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from ..types import (
    ChatAdminsSchema,
    ChatPatchSchema,
    PinMessageSchema,
    SendActionSchema,
    UserIdsSchema,
    build_request_payload,
)
from .base import BaseAPIGroup


class ChatsAPI(BaseAPIGroup):
    async def get_chats(self, count: Optional[int] = None, marker: Optional[int] = None) -> Any:
        params: Dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if marker is not None:
            params["marker"] = marker
        return await self._request_model("ChatList", "GET", "chats", params=params)

    async def get_chat_by_link(self, chat_link: str) -> Any:
        return await self._request_model("Chat", "GET", "chats/{0}".format(quote(chat_link, safe="@_-")))

    async def get_chat(self, chat_id: int) -> Any:
        return await self._request_model("Chat", "GET", "chats/{0}".format(chat_id))

    async def edit_chat(self, chat_id: int, patch: Union[Dict[str, Any], ChatPatchSchema]) -> Any:
        body = build_request_payload(patch, ChatPatchSchema)
        return await self._request_model("Chat", "PATCH", "chats/{0}".format(chat_id), json_body=body)

    async def delete_chat(self, chat_id: int) -> Any:
        return await self._request_model("SimpleQueryResult", "DELETE", "chats/{0}".format(chat_id))

    async def send_action(self, chat_id: int, action: Union[str, SendActionSchema]) -> Any:
        raw_body: Union[Dict[str, Any], SendActionSchema]
        if isinstance(action, SendActionSchema):
            raw_body = action
        else:
            raw_body = {"action": action}
        body = build_request_payload(raw_body, SendActionSchema)
        return await self._request_model(
            "SimpleQueryResult",
            "POST",
            "chats/{0}/actions".format(chat_id),
            json_body=body,
        )

    async def get_pinned_message(self, chat_id: int) -> Any:
        return await self._request_model("GetPinnedMessageResult", "GET", "chats/{0}/pin".format(chat_id))

    async def pin_message(self, chat_id: int, body: Union[Dict[str, Any], PinMessageSchema]) -> Any:
        payload = build_request_payload(body, PinMessageSchema)
        return await self._request_model(
            "SimpleQueryResult",
            "PUT",
            "chats/{0}/pin".format(chat_id),
            json_body=payload,
        )

    async def unpin_message(self, chat_id: int) -> Any:
        return await self._request_model("SimpleQueryResult", "DELETE", "chats/{0}/pin".format(chat_id))

    async def get_membership(self, chat_id: int) -> Any:
        return await self._request_model("ChatMember", "GET", "chats/{0}/members/me".format(chat_id))

    async def leave_chat(self, chat_id: int) -> Any:
        return await self._request_model("SimpleQueryResult", "DELETE", "chats/{0}/members/me".format(chat_id))

    async def get_admins(self, chat_id: int) -> Any:
        return await self._request_model("ChatMembersList", "GET", "chats/{0}/members/admins".format(chat_id))

    async def post_admins(self, chat_id: int, admins: Union[Dict[str, Any], ChatAdminsSchema]) -> Any:
        body = build_request_payload(admins, ChatAdminsSchema)
        return await self._request_model(
            "SimpleQueryResult",
            "POST",
            "chats/{0}/members/admins".format(chat_id),
            json_body=body,
        )

    async def delete_admins(self, chat_id: int, user_id: int) -> Any:
        return await self._request_model(
            "SimpleQueryResult",
            "DELETE",
            "chats/{0}/members/admins/{1}".format(chat_id, user_id),
        )

    async def get_members(
        self,
        chat_id: int,
        user_ids: Optional[List[int]] = None,
        marker: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Any:
        params: Dict[str, Any] = {}
        if user_ids:
            params["user_ids"] = ",".join([str(user_id) for user_id in user_ids])
        if marker is not None:
            params["marker"] = marker
        if count is not None:
            params["count"] = count
        return await self._request_model("ChatMembersList", "GET", "chats/{0}/members".format(chat_id), params=params)

    async def add_members(self, chat_id: int, users_body: Union[Dict[str, Any], UserIdsSchema]) -> Any:
        body = build_request_payload(users_body, UserIdsSchema)
        return await self._request_model(
            "SimpleQueryResult",
            "POST",
            "chats/{0}/members".format(chat_id),
            json_body=body,
        )

    async def remove_member(self, chat_id: int, user_id: int) -> Any:
        return await self._request_model(
            "SimpleQueryResult",
            "DELETE",
            "chats/{0}/members".format(chat_id),
            params={"user_id": user_id},
        )

    # OpenAPI parity aliases (operationId)
    getChats = get_chats
    getChatByLink = get_chat_by_link
    getChat = get_chat
    editChat = edit_chat
    deleteChat = delete_chat
    sendAction = send_action
    getPinnedMessage = get_pinned_message
    pinMessage = pin_message
    unpinMessage = unpin_message
    getMembership = get_membership
    leaveChat = leave_chat
    getAdmins = get_admins
    postAdmins = post_admins
    deleteAdmins = delete_admins
    getMembers = get_members
    addMembers = add_members
    removeMember = remove_member
