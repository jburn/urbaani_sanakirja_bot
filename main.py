"""
Main module for running the bot
"""
from os import getenv
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
from bot import get_application_handlers

def main():
    """
    Main function for running the bot
    """
    load_dotenv()
    token = getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Failed to get TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handlers(get_application_handlers())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
