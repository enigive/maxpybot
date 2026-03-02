"""API groups (bots, chats, messages, subscriptions, uploads)."""

from .bots import BotsAPI
from .chats import ChatsAPI
from .messages import MessagesAPI
from .subscriptions import SubscriptionsAPI
from .uploads import UploadsAPI

__all__ = ["BotsAPI", "ChatsAPI", "MessagesAPI", "SubscriptionsAPI", "UploadsAPI"]
