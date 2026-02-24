import aiohttp
import asyncio
import math
import re

CHUNK_SIZE = 1024 * 256  # 256KB


# =========================
# Utilidades
# =========================

def format_size(size: int) -> str:
    """Converte bytes para MB/GB"""
    if not size:
        return "Desconhecido"

    mb = size / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.2f} MB"

    gb = mb / 1024
    return f"{gb:.2f} GB"


def progress_bar(percent: float, length: int = 20) -> str:
    filled = int(length * percent / 100)
    return "█" * filled + "░" * (length - filled)


def extract_filename(headers, url: str) -> str:
    """Tenta pegar nome original do vídeo"""
    cd = headers.get("Content-Disposition")

    if cd:
        match = re.search('filename="?(.+?)"?$', cd)
        if match:
            return match.group(1)

    # fallback pelo link
    name = url.split("/")[-1].split("?")[0]

    if "." not in name:
        name += ".mp4"

    return name


# =========================
# Detectar vídeo real
# =========================

async def resolve_video_url(session, url: str):
    """
    Segue redirects e tenta descobrir se é vídeo real
    """
    async with session.get(url, allow_redirects=True) as resp:
        content_type = resp.headers.get("Content-Type", "").lower()

        # aceita vários tipos usados por CDNs
        if any(x in content_type for x in [
            "video",
            "octet-stream",
            "application/mp4",
            "binary"
        ]):
            return str(resp.url), resp.headers

        return None, None


# =========================
# STREAM PRINCIPAL
# =========================

async def stream_video(
    url: str,
    progress_callback=None
):
    """
    Faz download em streaming e retorna bytes do vídeo
    """

    timeout = aiohttp.ClientTimeout(total=None)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        # descobrir URL final do vídeo
        final_url, headers = await resolve_video_url(session, url)

        if not final_url:
            raise Exception("❌ O link não retornou um vídeo direto.")

        total_size = int(headers.get("Content-Length", 0))
        filename = extract_filename(headers, final_url)

        downloaded = 0
        last_update = 0

        data = bytearray()

        async with session.get(final_url) as resp:

            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                if not chunk:
                    continue

                data.extend(chunk)
                downloaded += len(chunk)

                # atualizar progresso a cada ~1%
                if total_size:
                    percent = (downloaded / total_size) * 100
                else:
                    percent = 0

                if progress_callback:
                    if percent - last_update >= 1:
                        last_update = percent

                        bar = progress_bar(percent)

                        await progress_callback(
                            filename,
                            downloaded,
                            total_size,
                            percent,
                            bar
                        )

        return bytes(data), filename, total_size
