import asyncio

from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher, F
from maxpybot.dispatcher.router import Router
from maxpybot.types import Message

BOT_TOKEN = "YOUR_BOT_TOKEN"


async def main() -> None:
    bot = MaxBot(BOT_TOKEN)
    dp = Dispatcher()
    router = Router()

    @router.message(F.text)
    async def on_text(message: Message) -> None:
        await bot.messages.send_message(
            body={"text": "Hello from maxpybot"},
            chat_id=message.chat.chat_id,
        )

    dp.include_router(router)
    await dp.start_polling(bot, types=["message_created", "message_callback"])


if __name__ == "__main__":
    asyncio.run(main())
