# Отправка сообщений: без JSON, с удобными методами

Начиная с текущей версии можно отправлять сообщения и вложения **без передачи `body`/dict** — через high-level методы `MaxBot`: `send_message`, `send_image`, `send_video`, …

Низкоуровневый API `bot.messages.send_message(body=...)` остаётся доступен, но для обычных сценариев он больше не нужен.

## TL;DR

```python
await bot.send_message(chat_id=message.chat.chat_id, text="Привет!")
```

## 1) Текст и форматирование

```python
await bot.send_message(
    chat_id=chat_id,
    text="**жирный**, *курсив*, `код`",
    format="markdown",  # или "html"
)
```

## 2) Фото

### Из файла (с автоматическим upload)

```python
await bot.send_image(chat_id=chat_id, file_path="local.jpg", caption="Фото")
```

### По внешнему URL (без upload)

```python
await bot.send_image(chat_id=chat_id, url="https://example.com/image.jpg", caption="Фото по ссылке")
```

### По token (если он у вас уже есть)

```python
await bot.send_image(chat_id=chat_id, token=existing_token, caption="Фото по token")
```

## 3) Видео / аудио / файл (с upload)

Видео:

```python
await bot.send_video(chat_id=chat_id, file_path="clip.mp4", caption="Видео")
```

Аудио:

```python
await bot.send_audio(chat_id=chat_id, file_path="voice.ogg", caption="Аудио")
```

Файл:

```python
await bot.send_file(chat_id=chat_id, file_path="report.pdf", caption="PDF")
```

Если источник — URL, библиотека скачает контент и загрузит его в MAX перед отправкой:

```python
await bot.send_video(chat_id=chat_id, url="https://example.com/video.mp4")
```

Если у вас уже есть `token` от upload:

```python
await bot.send_file(chat_id=chat_id, token=uploaded_token)
```

## 4) Стикер / контакт / геолокация / share-preview

Стикер:

```python
await bot.send_sticker(chat_id=chat_id, code="sticker-code")
```

Контакт:

```python
await bot.send_contact(chat_id=chat_id, name="Иван", vcf_phone="+79990000000")
```

Геолокация:

```python
await bot.send_location(chat_id=chat_id, latitude=55.751244, longitude=37.618423, text="Мы здесь")
```

Share (превью ссылки):

```python
await bot.send_share(chat_id=chat_id, url="https://example.com", text="Ссылка с превью")
```

## 5) Inline keyboard (типизированные кнопки)

Inline клавиатура задаётся типами из `maxpybot.types`:

```python
from maxpybot.types import InlineKeyboard, InlineCallbackButton, InlineChatButton

kb = InlineKeyboard.from_rows(
    InlineKeyboard.row(InlineCallbackButton(text="Нажми меня", payload="button1 pressed")),
    InlineKeyboard.row(InlineChatButton(text="Обсудить", chat_title="Message discussion")),
)

await bot.send_message(chat_id=chat_id, text="Сообщение с inline-клавиатурой", inline_keyboard=kb)
```

Поддерживаемые inline-кнопки:

- `InlineCallbackButton(text, payload, intent=None)`
- `InlineLinkButton(text, url)`
- `InlineRequestContactButton(text)`
- `InlineRequestGeoLocationButton(text, quick=None)`
- `InlineChatButton(text, chat_title, chat_description=None, start_payload=None, uuid=None)`
- `InlineMessageButton(text)`

## 6) Reply keyboard (типизированные кнопки)

```python
from maxpybot.types import ReplyKeyboard, ReplyMessageButton, ReplyGeoLocationButton, ReplyContactButton

kb = ReplyKeyboard.from_rows(
    ReplyKeyboard.row(
        ReplyMessageButton(text="Да", payload="yes"),
        ReplyMessageButton(text="Нет", payload="no"),
    ),
    ReplyKeyboard.row(
        ReplyGeoLocationButton(text="Отправить геолокацию"),
        ReplyContactButton(text="Отправить контакт"),
    ),
)

await bot.send_message(chat_id=chat_id, text="Выберите действие", reply_keyboard=kb)
```

## 7) Сокращения (Shortcuts) в объектах Message и Callback

Для удобства объекты `Message` и `Callback` содержат встроенные методы для ответа, которые автоматически подставляют `chat_id` и используют экземпляр бота.

### В сообщениях (Message)

Вместо `await bot.send_message(chat_id=message.chat.chat_id, ...)` можно писать:

```python
@router.message_created()
async def on_message(message: Message) -> None:
    # Ответ текстом
    await message.answer(text="Получил ваше сообщение!")
    
    # Ответ картинкой
    await message.answer_image(file_path="photo.jpg", caption="Вот фото")
    
    # Ответ видео/файлом/стикером и т.д.
    await message.answer_video(url="https://example.com/video.mp4")
    await message.answer_sticker(code="sticker-123")
```

Доступные методы: `answer`, `answer_image`, `answer_video`, `answer_audio`, `answer_file`, `answer_sticker`, `answer_contact`, `answer_location`, `answer_share`. Параметры идентичны методам `bot.send_*`.

### В колбэках (Callback)

Метод `answer` в объекте `Callback` теперь не требует обязательной передачи бота (он подтягивается автоматически):

```python
@router.message_callback()
async def on_callback(callback: Callback) -> None:
    # Бот подставится сам, если апдейт пришел через диспетчер
    await callback.answer(notification="Действие выполнено!")
```

## 8) Ответ на callback (кнопка типа callback)

## 8) Reply/forward без JSON

```python
await bot.send_message(chat_id=chat_id, text="Ответ", reply_to_message_id="m-123")
await bot.send_message(chat_id=chat_id, text="Форвард", forward_message_id="m-456")
```

## 9) Нюансы

- Для `audio/file/sticker/contact` по OpenAPI вложение должно быть **единственным** в сообщении — поэтому методы `send_audio/send_file/send_sticker/send_contact` специально не принимают keyboard-параметры.
- Если MAX вернул `attachment.not.ready`, внутри `bot.messages.send_message/edit_message` уже есть ретраи с backoff (иногда этого всё равно может не хватить — повторите позже).

