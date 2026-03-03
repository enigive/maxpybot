from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Dict, List, Optional

from .api.bots import BotsAPI
from .api.chats import ChatsAPI
from .api.messages import MessagesAPI
from .api.subscriptions import SubscriptionsAPI
from .api.uploads import UploadsAPI
from .compat.update_parser import UpdateParser
from .constants import (
    DEFAULT_API_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_POLL_PAUSE_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_UPDATES_LIMIT,
    DEFAULT_VERSION,
)
from .exceptions import EmptyTokenError, TimeoutError
from .transport.client import TransportClient

if TYPE_CHECKING:
    from aiohttp import web

    from .dispatcher.router import Router
    from .dispatcher.webhook import WebhookMetrics
    from .types import InlineKeyboard, PhotoTokens, ReplyKeyboard, UploadedInfo

UpdateHandler = Callable[[Any], None]


class MaxBot:
    """Main API client entrypoint."""

    def __init__(
        self,
        token: str,
        base_url: str = DEFAULT_API_URL,
        version: str = DEFAULT_VERSION,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        pause_seconds: int = DEFAULT_POLL_PAUSE_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        debug: bool = False,
        update_handler: Optional[UpdateHandler] = None,
        session: Any = None,
    ) -> None:
        if not token:
            raise EmptyTokenError("bot token is empty")

        self._transport = TransportClient(
            token=token,
            base_url=base_url,
            version=version,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            session=session,
        )
        self._update_parser = UpdateParser(debug=debug)

        self.pause_seconds = pause_seconds
        self.timeout_seconds = timeout_seconds
        self.max_updates_limit = DEFAULT_UPDATES_LIMIT
        self.max_retries = max_retries
        self.update_handler = update_handler

        self.bots = BotsAPI(self._transport)
        self.chats = ChatsAPI(self._transport)
        self.messages = MessagesAPI(self._transport)
        self.subscriptions = SubscriptionsAPI(self._transport)
        self.uploads = UploadsAPI(self._transport)

        # Go-like aliases
        self.Bots = self.bots
        self.Chats = self.chats
        self.Messages = self.messages
        self.Subscriptions = self.subscriptions
        self.Uploads = self.uploads

    async def __aenter__(self) -> "MaxBot":
        await self._transport.open()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._transport.close()

    def get_errors(self) -> "asyncio.Queue[Exception]":
        return self._transport.errors()

    async def get_updates(
        self,
        marker: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        limit: Optional[int] = None,
        types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if marker is not None:
            params["marker"] = str(marker)
        if timeout_seconds is not None:
            params["timeout"] = str(timeout_seconds)
        if limit is not None:
            params["limit"] = str(limit)
        if types:
            params["types"] = types

        try:
            return await self._transport.request_json(
                "GET",
                "updates",
                params=params,
                retry_attempts=self.max_retries,
            )
        except TimeoutError:
            # Mirror Go behavior: timeout during long polling is treated as empty page.
            return {"updates": [], "marker": marker}

    async def iter_updates(
        self,
        marker: Optional[int] = None,
        types: Optional[List[str]] = None,
    ) -> AsyncIterator[Any]:
        next_marker = marker
        while True:
            response = await self.get_updates(
                marker=next_marker,
                timeout_seconds=self.timeout_seconds,
                limit=self.max_updates_limit,
                types=types,
            )
            raw_updates = response.get("updates", [])
            for raw_update in raw_updates:
                update = self._update_parser.parse_update(raw_update, bot=self)
                if self.update_handler is not None:
                    self.update_handler(update)
                else:
                    yield update

            if response.get("marker") is not None:
                next_marker = response["marker"]

            if not raw_updates:
                await asyncio.sleep(self.pause_seconds)

    async def start_polling(
        self,
        router: "Router",
        marker: Optional[int] = None,
        types: Optional[List[str]] = None,
    ) -> None:
        from .dispatcher.polling import PollingRunner

        runner = PollingRunner(api=self, router=router)
        async with self:
            await runner.run(marker=marker, types=types)

    def create_webhook_app(
        self,
        router: "Router",
        path: str,
        secret: str = "",
        secret_header: str = "X-Max-Bot-Api-Secret",
        allowed_ip_networks: Optional[List[str]] = None,
        max_processing_retries: int = 0,
        metrics: Optional["WebhookMetrics"] = None,
    ) -> "web.Application":
        from .dispatcher.webhook import create_webhook_app

        return create_webhook_app(
            router=router,
            path=path,
            bot=self,
            secret=secret,
            secret_header=secret_header,
            allowed_ip_networks=allowed_ip_networks,
            max_processing_retries=max_processing_retries,
            metrics=metrics,
        )

    async def subscribe_webhook(
        self,
        subscribe_url: str,
        update_types: Optional[List[str]] = None,
        secret: str = "",
    ) -> Any:
        return await self.subscriptions.subscribe(
            subscribe_url=subscribe_url,
            update_types=update_types,
            secret=secret,
        )

    async def unsubscribe_webhook(self, subscription_url: str) -> Any:
        return await self.subscriptions.unsubscribe(subscription_url)

    async def unsubscribe_all_webhooks(self) -> Any:
        return await self.subscriptions.unsubscribe_all()

    def start_webhook(
        self,
        router: "Router",
        path: str,
        host: str = "127.0.0.1",
        port: int = 8443,
        cert_path: str = "",
        key_path: str = "",
        secret: str = "",
        secret_header: str = "X-Max-Bot-Api-Secret",
        allowed_ip_networks: Optional[List[str]] = None,
        max_processing_retries: int = 0,
        metrics: Optional["WebhookMetrics"] = None,
        subscribe_url: str = "",
        update_types: Optional[List[str]] = None,
        unsubscribe_on_shutdown: bool = False,
    ) -> None:
        from aiohttp import web

        from .dispatcher.webhook import create_https_ssl_context

        app = self.create_webhook_app(
            router=router,
            path=path,
            secret=secret,
            secret_header=secret_header,
            allowed_ip_networks=allowed_ip_networks,
            max_processing_retries=max_processing_retries,
            metrics=metrics,
        )

        async def _on_startup(_: web.Application) -> None:
            await self._transport.open()
            if subscribe_url:
                await self.subscribe_webhook(
                    subscribe_url=subscribe_url,
                    update_types=update_types,
                    secret=secret,
                )

        async def _on_cleanup(_: web.Application) -> None:
            if subscribe_url and unsubscribe_on_shutdown:
                await self.unsubscribe_webhook(subscribe_url)
            await self.close()

        app.on_startup.append(_on_startup)
        app.on_cleanup.append(_on_cleanup)

        ssl_context = None
        if cert_path and key_path:
            ssl_context = create_https_ssl_context(cert_path, key_path)

        web.run_app(app, host=host, port=port, ssl_context=ssl_context)

    async def send_message(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        text: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        attachments: List[Dict[str, Any]] = []
        attachments.extend(self._build_keyboard_attachments(inline_keyboard=inline_keyboard, reply_keyboard=reply_keyboard))
        body = self._build_new_message_body(
            text=text,
            attachments=attachments,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_image(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["PhotoTokens"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        image_attachment = await self._build_image_attachment(
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
        )
        attachments: List[Dict[str, Any]] = [image_attachment]
        attachments.extend(self._build_keyboard_attachments(inline_keyboard=inline_keyboard, reply_keyboard=reply_keyboard))
        body = self._build_new_message_body(
            text=caption,
            attachments=attachments,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_video(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["UploadedInfo"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        video_attachment = await self._build_uploaded_token_attachment(
            attachment_type="video",
            upload_type="video",
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
        )
        attachments: List[Dict[str, Any]] = [video_attachment]
        attachments.extend(self._build_keyboard_attachments(inline_keyboard=inline_keyboard, reply_keyboard=reply_keyboard))
        body = self._build_new_message_body(
            text=caption,
            attachments=attachments,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_audio(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["UploadedInfo"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        audio_attachment = await self._build_uploaded_token_attachment(
            attachment_type="audio",
            upload_type="audio",
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
        )
        body = self._build_new_message_body(
            text=caption,
            attachments=[audio_attachment],
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_file(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["UploadedInfo"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        file_attachment = await self._build_uploaded_token_attachment(
            attachment_type="file",
            upload_type="file",
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
        )
        body = self._build_new_message_body(
            text=caption,
            attachments=[file_attachment],
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_sticker(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        code: str = "",
        notify: bool = True,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        if not code:
            raise ValueError("sticker code is empty")
        body = self._build_new_message_body(
            text="",
            attachments=[{"type": "sticker", "payload": {"code": code}}],
            notify=notify,
            format=None,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_contact(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        name: str = "",
        contact_id: Optional[int] = None,
        vcf_phone: Optional[str] = None,
        vcf_info: Optional[str] = None,
        notify: bool = True,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        if not name:
            raise ValueError("contact name is empty")
        payload: Dict[str, Any] = {"name": name}
        if contact_id is not None:
            payload["contact_id"] = contact_id
        if vcf_phone is not None:
            payload["vcf_phone"] = vcf_phone
        if vcf_info is not None:
            payload["vcf_info"] = vcf_info

        body = self._build_new_message_body(
            text="",
            attachments=[{"type": "contact", "payload": payload}],
            notify=notify,
            format=None,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_location(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        latitude: float,
        longitude: float,
        text: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        location_attachment = {"type": "location", "latitude": latitude, "longitude": longitude}
        attachments: List[Dict[str, Any]] = [location_attachment]
        attachments.extend(self._build_keyboard_attachments(inline_keyboard=inline_keyboard, reply_keyboard=reply_keyboard))
        body = self._build_new_message_body(
            text=text,
            attachments=attachments,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    async def send_share(
        self,
        *,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        url: str,
        text: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        if not url:
            raise ValueError("share url is empty")
        share_attachment = {"type": "share", "payload": {"url": url}}
        attachments: List[Dict[str, Any]] = [share_attachment]
        attachments.extend(self._build_keyboard_attachments(inline_keyboard=inline_keyboard, reply_keyboard=reply_keyboard))
        body = self._build_new_message_body(
            text=text,
            attachments=attachments,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )
        return await self.messages.send_message(body=body, chat_id=chat_id, user_id=user_id)

    def _build_keyboard_attachments(
        self,
        *,
        inline_keyboard: Optional["InlineKeyboard"],
        reply_keyboard: Optional["ReplyKeyboard"],
    ) -> List[Dict[str, Any]]:
        if inline_keyboard is not None and reply_keyboard is not None:
            raise ValueError("only one keyboard can be attached: inline_keyboard or reply_keyboard")

        attachments: List[Dict[str, Any]] = []
        if inline_keyboard is not None:
            to_attachment = getattr(inline_keyboard, "to_attachment_request", None)
            if not callable(to_attachment):
                raise TypeError("inline_keyboard must be InlineKeyboard")
            attachments.append(to_attachment())
        if reply_keyboard is not None:
            to_attachment = getattr(reply_keyboard, "to_attachment_request", None)
            if not callable(to_attachment):
                raise TypeError("reply_keyboard must be ReplyKeyboard")
            attachments.append(to_attachment())
        return attachments

    def _build_new_message_body(
        self,
        *,
        text: str,
        attachments: List[Dict[str, Any]],
        notify: bool,
        format: Optional[str],
        reply_to_message_id: Optional[str],
        forward_message_id: Optional[str],
    ) -> Dict[str, Any]:
        link = self._build_message_link(reply_to_message_id=reply_to_message_id, forward_message_id=forward_message_id)
        body: Dict[str, Any] = {"text": text, "attachments": attachments, "link": link}
        if not notify:
            body["notify"] = False
        if format is not None:
            body["format"] = format
        return body

    def _build_message_link(
        self,
        *,
        reply_to_message_id: Optional[str],
        forward_message_id: Optional[str],
    ) -> Dict[str, Any]:
        if reply_to_message_id and forward_message_id:
            raise ValueError("only one of reply_to_message_id or forward_message_id can be set")
        if reply_to_message_id:
            return {"type": "reply", "mid": reply_to_message_id}
        if forward_message_id:
            return {"type": "forward", "mid": forward_message_id}
        return {}

    async def _build_image_attachment(
        self,
        *,
        file_path: Optional[str],
        url: Optional[str],
        token: Optional[str],
        uploaded: Optional[Any],
    ) -> Dict[str, Any]:
        mode = _pick_one(
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
        )
        if mode == "url":
            return {"type": "image", "payload": {"url": str(url)}}
        if mode == "token":
            return {"type": "image", "payload": {"token": str(token)}}
        if mode == "uploaded":
            photos = _extract_photos(uploaded)
            return {"type": "image", "payload": {"photos": photos}}

        uploaded_tokens = await self.uploads.upload_media_from_file("image", str(file_path))
        photos = _extract_photos(uploaded_tokens)
        return {"type": "image", "payload": {"photos": photos}}

    async def _build_uploaded_token_attachment(
        self,
        *,
        attachment_type: str,
        upload_type: str,
        file_path: Optional[str],
        url: Optional[str],
        token: Optional[str],
        uploaded: Optional[Any],
    ) -> Dict[str, Any]:
        mode = _pick_one(
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
        )
        if mode == "token":
            return {"type": attachment_type, "payload": {"token": str(token)}}
        if mode == "uploaded":
            resolved = _extract_token(uploaded)
            if not resolved:
                raise ValueError("uploaded token is empty")
            return {"type": attachment_type, "payload": {"token": resolved}}
        if mode == "url":
            uploaded_info = await self.uploads.upload_media_from_url(upload_type, str(url))
            resolved = _extract_token(uploaded_info)
            if not resolved:
                raise ValueError("upload result token is empty")
            return {"type": attachment_type, "payload": {"token": resolved}}

        uploaded_info = await self.uploads.upload_media_from_file(upload_type, str(file_path))
        resolved = _extract_token(uploaded_info)
        if not resolved:
            raise ValueError("upload result token is empty")
        return {"type": attachment_type, "payload": {"token": resolved}}

    getUpdates = get_updates
    iterUpdates = iter_updates


def _pick_one(**values: Any) -> str:
    provided = [name for name, value in values.items() if value is not None]
    if len(provided) != 1:
        raise ValueError("exactly one source must be provided: {0}".format(", ".join(values.keys())))
    return provided[0]


def _extract_token(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("token") or "")
    if hasattr(value, "token"):
        return str(getattr(value, "token") or "")
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(by_alias=True)
        if isinstance(dumped, dict):
            return str(dumped.get("token") or "")
    return ""


def _extract_photos(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        photos = value.get("photos")
        if isinstance(photos, dict):
            return photos
        return {}
    if hasattr(value, "photos"):
        photos = getattr(value, "photos")
        if isinstance(photos, dict):
            return photos
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(by_alias=True)
        if isinstance(dumped, dict):
            photos = dumped.get("photos")
            if isinstance(photos, dict):
                return photos
    return {}
