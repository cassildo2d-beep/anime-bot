import httpx
from io import BytesIO
from telegram import InputFile
from config import CHUNK_SIZE

async def stream_to_telegram(app, chat_id, url, filename):
    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            # mensagem inicial da barra de progresso
            progress_msg = await app.bot.send_message(chat_id, "⬇️ 0%")

            buffer = BytesIO()

            async for chunk in response.aiter_bytes(CHUNK_SIZE):
                buffer.write(chunk)
                downloaded += len(chunk)

                if total > 0:
                    percent = int(downloaded / total * 100)
                    try:
                        await progress_msg.edit_text(f"⬇️ {percent}%")
                    except Exception:
                        pass  # evita crash se edição falhar

            buffer.seek(0)
            await app.bot.send_document(
                chat_id=chat_id,
                document=InputFile(buffer, filename=filename)
            )
            await progress_msg.edit_text("✅ Upload concluído!")
