import httpx
import asyncio
import os
import time
from telegram import InputFile
from config import CHUNK_SIZE

BAR_SIZE = 20


def bar(p):
    filled = int(BAR_SIZE * p / 100)
    return "█" * filled + "░" * (BAR_SIZE - filled)


def size_fmt(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024


async def stream_to_telegram(app, chat_id, url, filename):

    temp_path = f"/tmp/{filename}"

    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:

            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            start = time.time()
            last_update = 0

            msg = await app.bot.send_message(
                chat_id,
                f"🎬 {filename}\n\nIniciando streaming..."
            )

            # abre arquivo temporário STREAMÁVEL
            with open(temp_path, "wb") as f:

                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()

                    # update a cada 2s
                    if now - last_update > 2 and total:
                        percent = int(downloaded * 100 / total)

                        elapsed = now - start
                        speed = downloaded / elapsed if elapsed else 0
                        eta = (total - downloaded) / speed if speed else 0

                        text = (
                            f"🎬 {filename}\n\n"
                            f"{bar(percent)} {percent}%\n"
                            f"📦 {size_fmt(downloaded)} / {size_fmt(total)}\n"
                            f"⚡ {size_fmt(speed)}/s\n"
                            f"⏳ ETA: {int(eta)}s"
                        )

                        try:
                            await msg.edit_text(text)
                        except:
                            pass

                        last_update = now

            # DOWNLOAD terminou → upload começa instantaneamente
            await app.bot.send_document(
                chat_id=chat_id,
                document=InputFile(temp_path, filename=filename)
            )

            await msg.edit_text("✅ Episódio enviado!")

    # limpa storage
    try:
        os.remove(temp_path)
    except:
        pass
