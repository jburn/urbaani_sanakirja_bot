from telegram.ext import ApplicationBuilder
from bot import get_application_handlers

def main():
    try:
        with open('./token', 'r') as tokenfile:
            TOKEN = tokenfile.read()
    except:
        print("Failed to open TOKEN file")
        exit(1)
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handlers(get_application_handlers())
    app.run_polling()

if __name__ == "__main__":
    main()
