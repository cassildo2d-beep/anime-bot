# streaming/stream_http.py
import aiohttp
import asyncio
import re

CHUNK_SIZE = 1024 * 256  # 256KB

BAR_SIZE = 20

def progress_bar(percent: float, length: int = 20) -> str:
    filled = int(length * percent / 100)
    return "█" * filled + "░" * (length - filled)

def format_size(size: int) -> str:
    if not size:
        return "Desconhecido"
    mb = size / (1024*1024)
    if mb < 1024:
        return f"{mb:.2f} MB"
    gb = mb / 1024
    return f"{gb:.2f} GB"

def extract_filename(headers, url: str) -> str:
    cd = headers.get("Content-Disposition")
    if cd:
        match = re.search('filename="?(.+?)"?$', cd)
        if match:
            return match.group(1)
    name = url.split("/")[-1].split("?")[0]
    if "." not in name:
        name += ".mp4"
    return name

async def stream_to_telegram(app, chat_id, url: str, progress_callback=None):
    """
    Função que substitui stream_video.
    Faz streaming real para o bot.
    """
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, allow_redirects=True) as resp:
            headers = resp.headers
            final_url = str(resp.url)
            total_size = int(headers.get("Content-Length", 0))
            filename = extract_filename(headers, final_url)

            downloaded = 0
            last_update = 0
            data = bytearray()

            # mensagem inicial no Telegram
            if progress_callback:
                await progress_callback(f"🎬 {filename}", 0, total_size, 0, progress_bar(0))

            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                if not chunk:
                    continue
                data.extend(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                else:
                    percent = 0
                if progress_callback and percent - last_update >= 1:
                    last_update = percent
                    bar = progress_bar(percent)
                    await progress_callback(filename, downloaded, total_size, percent, bar)

            # envia vídeo para o Telegram
            from telegram import InputFile
            import io
            bio = io.BytesIO(data)
            bio.name = filename
            bio.seek(0)
            await app.bot.send_video(
                chat_id=chat_id,
                video=InputFile(bio, filename=filename),
                supports_streaming=True
            )
