from core.queue_manager import DOWNLOAD_QUEUE
from streaming.stream_http import stream_to_telegram
from streaming.link_resolver import resolve_link

async def queue_worker(app):
    while True:
        task = await DOWNLOAD_QUEUE.get()
        try:
            url = await resolve_link(task["url"])
            await stream_to_telegram(
                app=app,
                chat_id=task["chat_id"],
                url=url,
                filename=task["filename"]
            )
        except Exception as e:
            print("Erro no worker:", e)
        DOWNLOAD_QUEUE.task_done()
