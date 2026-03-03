import asyncio

from maxpybot import MaxBot
from maxpybot.dispatcher import F
from maxpybot.dispatcher.router import Router
from maxpybot.fsm import FSMContext, MemoryStorage
from maxpybot.types import Message

BOT_TOKEN = "YOUR_BOT_TOKEN"

STATE_AWAIT_NAME = "feedback:await_name"
STATE_AWAIT_CONTACT = "feedback:await_contact"


async def main() -> None:
    bot = MaxBot(BOT_TOKEN)
    storage = MemoryStorage()
    router = Router(storage=storage)

    @router.message(F.text.startswith("/feedback"))
    async def on_feedback_start(message: Message, fsm: FSMContext) -> None:
        await fsm.clear()
        await fsm.set_state(STATE_AWAIT_NAME)
        await bot.send_message(chat_id=message.chat.chat_id, text="Как вас зовут?")

    @router.message_created(state=STATE_AWAIT_NAME)
    async def on_feedback_name(message: Message, fsm: FSMContext) -> None:
        name = message.body.text.strip()
        if not name:
            return

        await fsm.update_data(name=name)
        await fsm.set_state(STATE_AWAIT_CONTACT)
        await bot.send_message(chat_id=message.chat.chat_id, text="Оставьте email или телефон для связи.")

    @router.message_created(state=STATE_AWAIT_CONTACT)
    async def on_feedback_contact(message: Message, fsm: FSMContext) -> None:
        contact = message.body.text.strip()
        if not contact:
            return

        data = await fsm.get_data()
        user_name = str(data.get("name") or "друг")
        await fsm.clear()
        await bot.send_message(
            chat_id=message.chat.chat_id,
            text="Спасибо, {0}! Мы свяжемся: {1}".format(user_name, contact),
        )

    await bot.start_polling(router)


if __name__ == "__main__":
    asyncio.run(main())
