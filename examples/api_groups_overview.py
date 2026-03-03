import asyncio

from maxpybot import MaxBot

BOT_TOKEN = "YOUR_BOT_TOKEN"


async def main() -> None:
    bot = MaxBot(BOT_TOKEN)
    async with bot:
        # bots
        me = await bot.bots.get_my_info()
        print("Bot info:", me)

        # chats (example request)
        chats = await bot.chats.get_chats(count=20)
        print("Chats page:", chats)

        # messages (example request)
        messages = await bot.messages.get_messages(chat_id=1234567890, count=20)
        print("Messages page:", messages)

        # subscriptions
        subscriptions = await bot.subscriptions.get_subscriptions()
        print("Subscriptions:", subscriptions)

        # uploads
        upload_url = await bot.uploads.get_upload_url("file")
        print("Upload endpoint:", upload_url)


if __name__ == "__main__":
    asyncio.run(main())
