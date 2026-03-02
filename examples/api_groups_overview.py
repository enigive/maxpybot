import asyncio

from maxpybot import MaxBotAPI

BOT_TOKEN = "YOUR_BOT_TOKEN"


async def main() -> None:
    async with MaxBotAPI(BOT_TOKEN) as api:
        # bots
        me = await api.bots.get_my_info()
        print("Bot info:", me)

        # chats (example request)
        chats = await api.chats.get_chats(count=20)
        print("Chats page:", chats)

        # messages (example request)
        messages = await api.messages.get_messages(chat_id=1234567890, count=20)
        print("Messages page:", messages)

        # subscriptions
        subscriptions = await api.subscriptions.get_subscriptions()
        print("Subscriptions:", subscriptions)

        # uploads
        upload_url = await api.uploads.get_upload_url("file")
        print("Upload endpoint:", upload_url)


if __name__ == "__main__":
    asyncio.run(main())
