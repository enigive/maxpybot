import asyncio

from maxpybot import MaxBotAPI

BOT_TOKEN = "YOUR_BOT_TOKEN"


async def main() -> None:
    async with MaxBotAPI(BOT_TOKEN) as api:
        # Upload from local file.
        file_info = await api.uploads.upload_media_from_file("file", "path/to/local-file.bin")
        print("Uploaded file:", file_info)

        # Upload from remote URL.
        image_info = await api.uploads.upload_media_from_url("image", "https://example.com/image.jpg")
        print("Uploaded image:", image_info)


if __name__ == "__main__":
    asyncio.run(main())
