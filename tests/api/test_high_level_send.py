from typing import Any, Dict, Optional, Tuple

import pytest

from maxpybot import MaxBot
from maxpybot.types import (
    InlineCallbackButton,
    InlineKeyboard,
    PhotoTokens,
    ReplyKeyboard,
    ReplyMessageButton,
    UploadedInfo,
)


def _bind_capture_request_model(bot: MaxBot) -> Dict[str, Any]:
    captured: Dict[str, Any] = {}

    async def fake_request_model(  # noqa: ANN202
        model_name: str,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        authorized: bool = True,
        expected_statuses: Tuple[int, ...] = (200,),
    ) -> Dict[str, Any]:
        captured["model_name"] = model_name
        captured["method"] = method
        captured["path"] = path
        captured["params"] = params
        captured["json_body"] = json_body
        captured["authorized"] = authorized
        captured["expected_statuses"] = expected_statuses
        return captured

    bot.messages._request_model = fake_request_model  # type: ignore[method-assign]
    return captured


@pytest.mark.asyncio
async def test_maxbot_send_message_builds_body_without_json() -> None:
    bot = MaxBot("token")
    captured = _bind_capture_request_model(bot)

    await bot.send_message(chat_id=200, text="hello")

    assert captured["path"] == "messages"
    assert captured["params"] == {"chat_id": 200}
    assert captured["json_body"] == {"text": "hello", "attachments": []}


@pytest.mark.asyncio
async def test_maxbot_edit_message_builds_body() -> None:
    bot = MaxBot("token")
    captured = _bind_capture_request_model(bot)

    await bot.edit_message(message_id="m123", text="updated")

    assert captured["method"] == "PUT"
    assert captured["path"] == "messages"
    assert captured["params"] == {"message_id": "m123"}
    assert captured["json_body"] == {"text": "updated", "attachments": []}


def test_build_new_message_body_without_link() -> None:
    bot = MaxBot("token")

    body = bot._build_new_message_body(
        text="hello",
        attachments=[],
        notify=True,
        format=None,
        reply_to_message_id=None,
        forward_message_id=None,
    )

    assert "link" not in body


def test_build_new_message_body_with_reply_link() -> None:
    bot = MaxBot("token")

    body = bot._build_new_message_body(
        text="reply",
        attachments=[],
        notify=True,
        format=None,
        reply_to_message_id="m-1",
        forward_message_id=None,
    )

    assert body["link"] == {"type": "reply", "mid": "m-1"}


@pytest.mark.asyncio
async def test_maxbot_send_message_supports_reply_to() -> None:
    bot = MaxBot("token")
    captured = _bind_capture_request_model(bot)

    await bot.send_message(chat_id=200, text="reply", reply_to_message_id="m-1")

    assert captured["json_body"]["link"] == {"type": "reply", "mid": "m-1"}


@pytest.mark.asyncio
async def test_maxbot_send_message_with_inline_keyboard() -> None:
    bot = MaxBot("token")
    captured = _bind_capture_request_model(bot)

    kb = InlineKeyboard.from_rows(
        InlineKeyboard.row(InlineCallbackButton(text="OK", payload="ok")),
    )

    await bot.send_message(chat_id=200, text="hi", inline_keyboard=kb)

    assert captured["json_body"]["attachments"] == [
        {"type": "inline_keyboard", "payload": {"buttons": [[{"type": "callback", "text": "OK", "payload": "ok"}]]}}
    ]


@pytest.mark.asyncio
async def test_maxbot_send_message_rejects_two_keyboards() -> None:
    bot = MaxBot("token")
    _bind_capture_request_model(bot)

    inline = InlineKeyboard.from_rows(InlineKeyboard.row(InlineCallbackButton(text="OK", payload="ok")))
    reply = ReplyKeyboard.from_rows(ReplyKeyboard.row(ReplyMessageButton(text="Yes", payload="yes")))

    with pytest.raises(ValueError, match="only one keyboard"):
        await bot.send_message(chat_id=1, text="x", inline_keyboard=inline, reply_keyboard=reply)


@pytest.mark.asyncio
async def test_maxbot_send_image_uploads_file_and_builds_payload() -> None:
    bot = MaxBot("token")
    captured = _bind_capture_request_model(bot)
    calls: Dict[str, Any] = {}

    async def fake_upload_media_from_file(upload_type: str, file_path: str) -> PhotoTokens:
        calls["upload"] = (upload_type, file_path)
        return PhotoTokens.model_validate({"photos": {"p": {"token": "t1"}}})

    bot.uploads.upload_media_from_file = fake_upload_media_from_file  # type: ignore[method-assign]

    await bot.send_image(chat_id=200, file_path="local.jpg", caption="cap")

    assert calls["upload"] == ("image", "local.jpg")
    assert captured["json_body"]["text"] == "cap"
    assert captured["json_body"]["attachments"] == [
        {"type": "image", "payload": {"photos": {"p": {"token": "t1"}}}}
    ]


@pytest.mark.asyncio
async def test_maxbot_send_video_uploads_from_url_and_builds_payload() -> None:
    bot = MaxBot("token")
    captured = _bind_capture_request_model(bot)
    calls: Dict[str, Any] = {}

    async def fake_upload_media_from_url(upload_type: str, url: str) -> UploadedInfo:
        calls["upload"] = (upload_type, url)
        return UploadedInfo.model_validate({"token": "v1"})

    bot.uploads.upload_media_from_url = fake_upload_media_from_url  # type: ignore[method-assign]

    await bot.send_video(chat_id=200, url="https://example.com/video.mp4")

    assert calls["upload"] == ("video", "https://example.com/video.mp4")
    assert captured["json_body"]["attachments"] == [{"type": "video", "payload": {"token": "v1"}}]


@pytest.mark.asyncio
async def test_maxbot_send_audio_requires_exactly_one_source() -> None:
    bot = MaxBot("token")
    _bind_capture_request_model(bot)

    with pytest.raises(ValueError, match="exactly one source"):
        await bot.send_audio(chat_id=1, file_path="a.ogg", token="t")

