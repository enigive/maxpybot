import asyncio
from typing import Any, Dict

from maxpybot import MaxBotAPI
from maxpybot.dispatcher.filters import text_contains
from maxpybot.dispatcher.polling import PollingRunner
from maxpybot.dispatcher.router import Router

BOT_TOKEN = "YOUR_BOT_TOKEN"


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True)
    return {}


async def main() -> None:
    api = MaxBotAPI(BOT_TOKEN)
    router = Router()

    @router.message(text_contains("/start"))
    async def on_start(update: Any) -> None:
        update_dict = _as_dict(update)
        message = _as_dict(update_dict.get("message"))
        recipient = _as_dict(message.get("recipient"))
        chat_id = recipient.get("chat_id")
        if chat_id is None:
            return

        await api.messages.send_message(
            body={"text": "Hello from maxpybot"},
            chat_id=int(chat_id),
        )

    async with api:
        await PollingRunner(api, router).run(types=["message_created", "message_callback"])


if __name__ == "__main__":
    asyncio.run(main())
