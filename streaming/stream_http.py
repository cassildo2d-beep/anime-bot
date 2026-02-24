import httpx
import os
import re
import time

from telegram import InputFile
from config import CHUNK_SIZE

BAR_SIZE = 20


# =====================
# UTILIDADES
# =====================

def progress_bar(percent):
    filled = int(BAR_SIZE * percent / 100)
    return "█" * filled + "░" * (BAR_SIZE - filled)


def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def extract_filename(headers, url):
    cd = headers.get("Content-Disposition")
    if cd:
        match = re.search(r'filename="?([^"]+)"?', cd)
        if match:
            return match.group(1)

    name = url.split("/")[-1].split("?")[0]
    if "." not in name:
        name += ".mp4"
    return name


# =====================
# STREAM PRINCIPAL
# =====================

async def stream_to_telegram(app, chat_id, url, filename=None):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Range": "bytes=0-"  # 🔥 FORÇA STREAMING REAL
    }

    async with httpx.AsyncClient(
        timeout=None,
        follow_redirects=True,
        headers=headers
    ) as client:

        # resolve redirects primeiro
        r = await client.get(url)
        final_url = str(r.url)

        async with client.stream("GET", final_url) as response:

            content_type = response.headers.get("Content-Type", "")
            if "video" not in content_type and "octet-stream" not in content_type:
                await app.bot.send_message(
                    chat_id,
                    "❌ O link não retornou um vídeo direto."
                )
                return

            real_filename = filename or extract_filename(
                response.headers, final_url
            )

            total = int(response.headers.get("Content-Length", 0))

            temp_path = f"/tmp/{real_filename}"

            downloaded = 0
            start_time = time.time()
            last_update = 0

            progress_msg = await app.bot.send_message(
                chat_id,
                f"🎬 **{real_filename}**\n\nIniciando streaming...",
                parse_mode="Markdown"
            )

            # =====================
            # DOWNLOAD STREAMING
            # =====================

            with open(temp_path, "wb") as f:

                async for chunk in response.aiter_bytes(CHUNK_SIZE):

                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()

                    if total and now - last_update > 2:

                        percent = int(downloaded * 100 / total)

                        elapsed = now - start_time
                        speed = downloaded / elapsed if elapsed else 0
                        eta = (total - downloaded) / speed if speed else 0

                        text = (
                            f"🎬 **{real_filename}**\n\n"
                            f"{progress_bar(percent)} {percent}%\n\n"
                            f"📦 {format_size(downloaded)} / {format_size(total)}\n"
                            f"⚡ {format_size(speed)}/s\n"
                            f"⏳ ETA: {int(eta)}s"
                        )

                        try:
                            await progress_msg.edit_text(
                                text,
                                parse_mode="Markdown"
                            )
                        except:
                            pass

                        last_update = now

            # =====================
            # ENVIO TELEGRAM
            # =====================

            await progress_msg.edit_text(
                "📤 Enviando episódio para o Telegram..."
            )

            with open(temp_path, "rb") as video_file:

                await app.bot.send_video(
                    chat_id=chat_id,
                    video=InputFile(video_file, filename=real_filename),
                    supports_streaming=True
                )

            await progress_msg.edit_text("✅ Episódio enviado!")

    # =====================
    # LIMPEZA
    # =====================

    try:
        os.remove(temp_path)
    except:
        pass
        
