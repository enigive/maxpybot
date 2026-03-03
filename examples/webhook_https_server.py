from maxpybot import MaxBot
from maxpybot.dispatcher.router import Router
from maxpybot.types import Message

BOT_TOKEN = "YOUR_BOT_TOKEN"
WEBHOOK_URL = "https://bot.example.com/webhook"
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "CHANGE_ME"


def main() -> None:
    bot = MaxBot(BOT_TOKEN)
    router = Router()

    @router.message_created()
    async def on_message(message: Message) -> None:
        await bot.send_message(chat_id=message.chat.chat_id, text="Webhook is active")

    bot.start_webhook(
        router=router,
        path=WEBHOOK_PATH,
        host="127.0.0.1",
        port=8443,
        cert_path="cert.pem",
        key_path="key.pem",
        secret=WEBHOOK_SECRET,
        subscribe_url=WEBHOOK_URL,
        unsubscribe_on_shutdown=True,
    )


if __name__ == "__main__":
    main()
