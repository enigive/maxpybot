"""MAX API compatibility helpers."""

from .attachments import normalize_message_attachments, parse_attachment
from .capabilities import CAPABILITY_MATRIX, detect_payload_capabilities, supported_capabilities
from .update_parser import UpdateParser

__all__ = [
    "UpdateParser",
    "parse_attachment",
    "normalize_message_attachments",
    "CAPABILITY_MATRIX",
    "detect_payload_capabilities",
    "supported_capabilities",
]
