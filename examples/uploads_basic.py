import asyncio

from maxpybot import MaxBot

BOT_TOKEN = "YOUR_BOT_TOKEN"


async def main() -> None:
    bot = MaxBot(BOT_TOKEN)
    async with bot:
        # Upload from local file.
        file_info = await bot.uploads.upload_media_from_file("file", "path/to/local-file.bin")
        print("Uploaded file:", file_info)

        # Upload from remote URL.
        image_info = await bot.uploads.upload_media_from_url("image", "https://example.com/image.jpg")
        print("Uploaded image:", image_info)


if __name__ == "__main__":
    asyncio.run(main())
