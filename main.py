"""
Main module for running the bot
"""
import asyncio
import logging
from os import getenv
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
from bot import get_application_handlers, periodic_scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("urbaani_sanakirja_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """
    Main function for running the bot
    """
    load_dotenv()
    token = getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Failed to get TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handlers(get_application_handlers())

    await app.initialize()
    await app.start()

    asyncio.create_task(periodic_scrape())

    try:
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
