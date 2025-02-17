import database
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

with open('./token', 'r') as tokenfile:
    TOKEN = tokenfile.read()


async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def button(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    print(query)
        
async def word_handler(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    words = database.get_definitions(update.message.text)
    if not words:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sanaa ei löytynyt")
        return
    keyboard = [
            [telegram.InlineKeyboardButton("Previous", callback_data="prev")],
            [telegram.InlineKeyboardButton(f"1/{len(words)}")],
            [telegram.InlineKeyboardButton("Next", callback_data="next")]
        ]
    
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    word = words[0]
    title = word[2]
    explanation = word[3]
    examples = word[4]
    user = word[5]
    date = word[6]
    likes = word[7]
    dislikes = word[8]
    labels = list(word[9])
    out_str =\
f"""Käyttäjältä: {user} | <i>Postattu {date}</i>\n<b>{title}</b>\n\nℹ️ <b>Selitys</b>\n{explanation}\n\n📍<b>Esimerkit</b>\n<i>{examples}</i>
"""
    #update.message.reply_text("hello", reply_markup=reply_markup)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=out_str, reply_markup=reply_markup) #parse_mode=telegram.constants.ParseMode.HTML,""" 

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, word_handler))
app.run_polling()
