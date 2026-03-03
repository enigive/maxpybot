import asyncio
from typing import List

from maxpybot import MaxBot

BOT_TOKEN = "YOUR_BOT_TOKEN"
WEBHOOK_URL = "https://bot.example.com/webhook"

UPDATE_TYPES: List[str] = [
    "message_created",
    "message_callback",
    "message_edited",
    "message_removed",
    "bot_added",
    "bot_removed",
    "dialog_muted",
    "dialog_unmuted",
    "dialog_cleared",
    "dialog_removed",
    "user_added",
    "user_removed",
    "bot_started",
    "bot_stopped",
    "chat_title_changed",
]


async def main() -> None:
    bot = MaxBot(BOT_TOKEN)
    async with bot:
        print("Create/refresh webhook subscription...")
        result = await bot.subscribe_webhook(
            subscribe_url=WEBHOOK_URL,
            update_types=UPDATE_TYPES,
            secret="CHANGE_ME",
        )
        print(result)

        print("Current subscriptions...")
        subscriptions = await bot.subscriptions.get_subscriptions()
        print(subscriptions)

        print("Unsubscribe one webhook...")
        single = await bot.unsubscribe_webhook(WEBHOOK_URL)
        print(single)

        print("Unsubscribe all webhooks...")
        all_removed = await bot.unsubscribe_all_webhooks()
        print(all_removed)


if __name__ == "__main__":
    asyncio.run(main())
