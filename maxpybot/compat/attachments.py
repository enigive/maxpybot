from __future__ import annotations

from typing import Any, Dict, Optional

from ..types import AttachmentType
from ..types.generated.runtime import validate_with_model


ATTACHMENT_MODEL_BY_TYPE = {
    AttachmentType.IMAGE: "PhotoAttachment",
    AttachmentType.VIDEO: "VideoAttachment",
    AttachmentType.AUDIO: "AudioAttachment",
    AttachmentType.FILE: "FileAttachment",
    AttachmentType.CONTACT: "ContactAttachment",
    AttachmentType.STICKER: "StickerAttachment",
    AttachmentType.SHARE: "ShareAttachment",
    AttachmentType.LOCATION: "LocationAttachment",
    AttachmentType.INLINE_KEYBOARD: "InlineKeyboardAttachment",
}


def parse_attachment(raw_attachment: Dict[str, Any]) -> Any:
    attachment_type = _to_attachment_type(raw_attachment.get("type"))
    if attachment_type is None:
        return raw_attachment
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


def _to_attachment_type(value: Any) -> Optional[AttachmentType]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return AttachmentType(raw)
    except ValueError:
        return None
