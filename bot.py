"""
Bot functionality module for urbaani_sanakirja_bot
"""
import asyncio
from uuid import uuid4
from telegram import (
    Update,
    constants,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    InlineQueryHandler
)
from word_database import WordDatabase
from scraper import scan_for_links, scan_for_words

database = WordDatabase()

async def run_scraper():
    """
    Run scraper to get words for backend
    """
    links = await scan_for_links()
    await scan_for_words(links, database)

async def periodic_scrape():
    """
    Periodically scrape for new words to add to database
    """
    while True:
        try:
            await run_scraper()
        except Exception as e:
            print(f"Exception when scraping: {e}")
        await asyncio.sleep(7 * 24 * 60 * 60)

def build_reply(word: tuple) -> str:
    """
    Format reply string when given a word object

    returns: formatted reply string
    """
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
    reply += "ℹ️ <b>Selitys</b>\n"
    reply += f"{explanation}\n\n"
    if examples:
        reply += "📍<b>Esimerkit</b>\n"
        reply += f"<i>{examples}</i>\n\n"
    reply += f"👍 {likes} | 👎 {dislikes}\n"
    return reply

def build_keyboard(definitions: list, current_index: int) -> InlineKeyboardMarkup:
    """
    Format inline keyboard markup when giving a reply

    returns: InlineKeyboardMarkup for message or None if keyboard is not needed
    """
    word = definitions[current_index][1]
    total = len(definitions)
    if len(definitions) <= 1:
        # no need for buttons if there is only 1 definition
        return None
    prev_i = (current_index - 1) % total
    next_i = (current_index + 1) % total
    prev_button = InlineKeyboardButton(
        "⬅️ Previous", callback_data=f"def:{word}:{prev_i}"
    )
    next_button = InlineKeyboardButton(
        "Next ➡️", callback_data=f"def:{word}:{next_i}"
    )
    middle_button = InlineKeyboardButton(f"{current_index + 1}/{total}", callback_data="none")

    keyboard = [[prev_button, middle_button, next_button]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext) -> None: # pylint: disable=W0613
    """
    Greeting message for user interacting with the bot for the first time
    """
    await update.message.reply_text(
        f"Moro {update.effective_user.first_name}! Lähetä minulle jokin sana, niin yritän etsiä sille selityksen." # pylint: disable=C0301
        )

async def word_handler(update: Update, context: CallbackContext): # pylint: disable=W0613
    """
    Handle word input from the user
    """
    definitions = database.get_definitions(update.message.text)
    if not definitions:
        await update.message.reply_text("Sanaa ei löytynyt")
        return
    index = 0
    out_str = build_reply(definitions[index])
    keyboard = build_keyboard(definitions, index)

    await update.message.reply_text(
        out_str,
        reply_markup=keyboard,
        parse_mode=constants.ParseMode.HTML
        )

async def callback_handler(update: Update, context: CallbackContext): # pylint: disable=W0613
    """
    Handle inline keyboard button callback data
    """
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
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode=constants.ParseMode.HTML
        )

async def inline_query(update: Update, context: CallbackContext): # pylint: disable=W0613
    """
    Handle the inline querying of words
    """
    query = update.inline_query.query.strip().lower()

    if not query:
        return

    definitions = database.get_definitions(query)

    if not definitions:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Ei tuloksia",
                input_message_content=InputTextMessageContent(
                    f"Selityksiä ei löytynyt sanalle '{query}'."
                    )
            )
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id = str(uuid4()),
                title = f"Selitys #{i+1}",
                description = explanation[:50] + "..." if len(explanation) > 50 else explanation,
                input_message_content = InputTextMessageContent(
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
            for i, (id,
                    word,
                    title,
                    explanation,
                    example,
                    user,
                    date,
                    likes,
                    dislikes,
                    labels) in enumerate(definitions)
        ]
    await update.inline_query.answer(results, cache_time=1)

def get_application_handlers():
    """
    Return all the handlers for the bot functionalities

    returns: list of handlers
    """
    return [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT, word_handler),
        CallbackQueryHandler(callback_handler, pattern=r"(def:|none)"),
        InlineQueryHandler(inline_query)
    ]
