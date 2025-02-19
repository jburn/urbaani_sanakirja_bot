from word_database import WordDatabase
from telegram import Update, constants, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, InlineQueryHandler
from uuid import uuid4


database = WordDatabase()

with open('./token', 'r') as tokenfile:
    TOKEN = tokenfile.read()

def build_reply(word: str) -> str:
    title = word[2]
    explanation = word[3]
    examples = word[4]
    user = word[5]
    date = word[6]
    likes = word[7]
    dislikes = word[8]
    reply = ""
    reply += f"Käyttäjältä: {user} | <i>Postattu {date}</i>\n"
    reply += f"<b>{title}</b>\n\n"
    reply += f"ℹ️ <b>Selitys</b>\n"
    reply += f"{explanation}\n\n"
    if examples:
        reply += f"📍<b>Esimerkit</b>\n"
        reply += f"<i>{examples}</i>\n\n"
    reply += f"👍 {likes} | 👎 {dislikes}\n"
    return reply


def build_keyboard(definitions: list, current_index: int) -> InlineKeyboardMarkup:
    word = definitions[current_index][1]
    total = len(definitions)
    if len(definitions) <= 1:
        # no need for buttons if there is only 1 definition
        return
    prev = (current_index - 1) % total
    next = (current_index + 1) % total
    prev_button = InlineKeyboardButton(
        "⬅️ Previous", callback_data=f"def:{word}:{prev}"
    )
    next_button = InlineKeyboardButton(
        "Next ➡️", callback_data=f"def:{word}:{next}"
    )
    middle_button = InlineKeyboardButton(f"{current_index + 1}/{total}", callback_data="none")

    keyboard = [[prev_button, middle_button, next_button]]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f'Moro {update.effective_user.first_name}! Lähetä minulle jokin sana, niin yritän etsiä sille selityksen.')
 

async def word_handler(update: Update, context: CallbackContext):
    definitions = database.get_definitions(update.message.text)
    if not definitions:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sanaa ei löytynyt")
        return None
    index = 0
    out_str = build_reply(definitions[index])
    keyboard = build_keyboard(definitions, index)

    await update.message.reply_text(out_str, reply_markup=keyboard, parse_mode=constants.ParseMode.HTML) 


async def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "none":
        return
    
    try:
        _, word, index_str = query.data.split(":")
        index = int(index_str)
    except ValueError:
        await query.edit_message_text("Invalid callback data")
        return
    
    definitions = database.get_definitions(word)
    if not definitions:
        await query.edit_message_text("Sanaa ei löytynyt")
        return
    
    index %= len(definitions)

    message = build_reply(definitions[index])
    keyboard = build_keyboard(definitions, index)
    await query.edit_message_text(message, reply_markup=keyboard, parse_mode=constants.ParseMode.HTML)

async def inline_query(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip().lower()

    if not query:
        return
    
    definitions = database.get_definitions(query)

    if not definitions:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Ei tuloksia",
                input_message_content=InputTextMessageContent(f"Selityksiä ei löytynyt sanalle '{query}'.")
            )
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Selitys #{i+1}",
                description=explanation[:50] + "...",  # Short preview
                input_message_content=InputTextMessageContent(
                    f"Käyttäjältä: {user} | <i>Postattu {date}</i>\n"
                    f"<b>{title}</b>\n\n"
                    f"ℹ️ <b>Selitys</b>\n"
                    f"{explanation}\n\n"
                    f"📍<b>Esimerkit</b>\n"
                    f"<i>{example if example else 'N/A'}</i>\n\n"
                    f"👍 {likes} | 👎 {dislikes}\n",
                    parse_mode="HTML"
                )
            )
            for i, (id, word, title, explanation, example, user, date, likes, dislikes, labels) in enumerate(definitions)
        ]
    
    await update.inline_query.answer(results, cache_time=1)
    

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, word_handler))
    app.add_handler(CallbackQueryHandler(callback_handler, pattern=r"(def:|none)"))
    app.add_handler(InlineQueryHandler(inline_query))
    app.run_polling()

if __name__ == "__main__":
    main()
    database.close()