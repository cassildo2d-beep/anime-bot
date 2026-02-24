import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

from config import BOT_TOKEN
from handlers.commands import start, anime, fila
from core.worker import queue_worker


async def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("anime", anime))
    app.add_handler(CommandHandler("fila", fila))

    asyncio.create_task(queue_worker(app))

    print("Bot iniciado...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
