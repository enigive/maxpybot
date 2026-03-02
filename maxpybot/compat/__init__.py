"""MAX API compatibility helpers."""

from .attachments import normalize_message_attachments, parse_attachment
from .update_parser import UpdateParser

__all__ = ["UpdateParser", "parse_attachment", "normalize_message_attachments"]
