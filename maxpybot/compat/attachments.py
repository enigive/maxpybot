from __future__ import annotations

from typing import Any, Dict

from ..types.generated.runtime import validate_with_model


ATTACHMENT_MODEL_BY_TYPE = {
    "image": "PhotoAttachment",
    "video": "VideoAttachment",
    "audio": "AudioAttachment",
    "file": "FileAttachment",
    "contact": "ContactAttachment",
    "sticker": "StickerAttachment",
    "share": "ShareAttachment",
    "location": "LocationAttachment",
    "inline_keyboard": "InlineKeyboardAttachment",
}


def parse_attachment(raw_attachment: Dict[str, Any]) -> Any:
    attachment_type = str(raw_attachment.get("type") or "")
    model_name = ATTACHMENT_MODEL_BY_TYPE.get(attachment_type)
    if not model_name:
        return raw_attachment
    return validate_with_model(model_name, raw_attachment)


def normalize_message_attachments(message_payload: Dict[str, Any]) -> Dict[str, Any]:
    body = message_payload.get("body")
    if not isinstance(body, dict):
        return message_payload

    raw_attachments = body.get("attachments")
    if not isinstance(raw_attachments, list):
        raw_attachments = body.get("raw_attachments")
    if isinstance(raw_attachments, list):
        body["attachments"] = [
            parse_attachment(item) if isinstance(item, dict) else item for item in raw_attachments
        ]

    link = message_payload.get("link")
    if isinstance(link, dict):
        linked_message = link.get("message")
        if isinstance(linked_message, dict):
            normalize_message_attachments(linked_message)

    return message_payload
