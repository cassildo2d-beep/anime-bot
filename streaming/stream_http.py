import httpx
from telegram import InputFile
from config import CHUNK_SIZE


async def stream_to_telegram(app, chat_id, url, filename):

    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:

        async with client.stream("GET", url) as response:

            async def generator():
                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    yield chunk

            await app.bot.send_document(
                chat_id=chat_id,
                document=InputFile(generator(), filename=filename)
            )
