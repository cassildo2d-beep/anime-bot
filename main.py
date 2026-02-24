from telegram.ext import ApplicationBuilder, CommandHandler

from config import BOT_TOKEN
from handlers.commands import start, anime, fila
from core.worker import queue_worker


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("anime", anime))
    app.add_handler(CommandHandler("fila", fila))

    # iniciar worker quando bot ligar
    async def post_init(application):
        application.create_task(queue_worker(application))

    app.post_init = post_init

    print("Bot iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
