from telegram.ext import ApplicationBuilder
from bot import get_application_handlers
from os import getenv
from dotenv import load_dotenv

def main():
    load_dotenv()
    TOKEN = getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Failed to get TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handlers(get_application_handlers())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
