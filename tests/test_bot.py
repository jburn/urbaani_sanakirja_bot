"""
Tests for the bot functionality module
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from telegram import (
    Update,
    CallbackQuery,
    InlineQuery,
    InlineKeyboardMarkup,
    constants,
    InlineQueryResultArticle
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    CallbackQueryHandler
)
from bot import (
    build_keyboard,
    build_reply,
    start,
    callback_handler,
    word_handler,
    inline_query,
    get_application_handlers,
    database
)

# import bot for mock monkeypatching
import bot


# Test helper functions
# Test build reply
@pytest.mark.parametrize(
    "word, expected_reply",
    [
        # Word with examples (should return reply with examples)
        (
            (1, 'word', 'Word', 'Definition of word', 'Example of word usage',
             'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
            ("Käyttäjältä: User | <i>Postattu dd.mm.yyyy</i>\n"
            "<b>Word</b>\n\n"
            "ℹ️ <b>Selitys</b>\n"
            "Definition of word\n\n"
            "📍<b>Esimerkit</b>\n"
            "<i>Example of word usage</i>\n\n"
            "👍 10 | 👎 10\n"
            )
        ),
        # Word without examples (should return reply without examples)
        (
            (1, 'word', 'Word', 'Definition of word', '',
             'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
            ("Käyttäjältä: User | <i>Postattu dd.mm.yyyy</i>\n"
            "<b>Word</b>\n\n"
            "ℹ️ <b>Selitys</b>\n"
            "Definition of word\n\n"
            "👍 10 | 👎 10\n"
            )
        ),

    ]
)
def test_build_reply(word, expected_reply):
    """
    Test that reply formatting works correctly
    """
    result = build_reply(word)
    assert expected_reply == result

# Test build keyboard
@pytest.mark.parametrize(
    "definitions, current_index, expected_prev, expected_next, expected_middle",
    [
        # Test multiple definitions (current index: 0)
        ([("id1", "word1"), ("id2", "word1"), ("id3", "word1")], 0, 2, 1, "1/3"),

        # Test multiple definitions (current index: 1)
        ([("id1", "word1"), ("id2", "word2"), ("id3", "word3")], 1, 0, 2, "2/3"),

        # Test multiple definitions (current index: 2, should wrap around)
        ([("id1", "word1"), ("id2", "word2"), ("id3", "word3")], 2, 1, 0, "3/3"),

        # Test single definition (should return None)
        ([("id1", "word1")], 0, None, None, None),

    ],
)
def test_build_keyboard(definitions, current_index, expected_prev, expected_next, expected_middle):
    """
    Test building reply markup keyboard works correctly
    """
    keyboard = build_keyboard(definitions, current_index)

    if len(definitions) <= 1:
        assert keyboard is None
    else:
        assert isinstance(keyboard, InlineKeyboardMarkup)
        buttons = keyboard.inline_keyboard[0]

        prev_button, middle_button, next_button = buttons
        word = definitions[current_index][1]

        assert prev_button.text == "⬅️ Previous"
        assert prev_button.callback_data == f"def:{word}:{expected_prev}"

        assert middle_button.text == expected_middle
        assert middle_button.callback_data == "none"

        assert next_button.text == "Next ➡️"
        assert next_button.callback_data == f"def:{word}:{expected_next}"

@pytest.mark.asyncio
async def test_start():
    """
    Test /start command handler
    """
    mock_user = MagicMock()
    mock_user.first_name = "TestName"

    mock_message = AsyncMock()
    mock_message.reply_text = AsyncMock()

    mock_update = MagicMock(spec=Update)
    mock_update.effective_user = mock_user
    mock_update.message = mock_message

    mock_context = MagicMock(spec=CallbackContext)

    await start(mock_update, mock_context)

    mock_message.reply_text.assert_called_once_with(
        f"Moro {mock_user.first_name}! "
        "Lähetä minulle jokin sana, niin yritän etsiä sille selityksen."
    )

# Test word handler
@pytest.mark.asyncio
async def test_word_handler_no_definition_found(monkeypatch):
    """
    Test message handler when no definitions are found in database
    """
    monkeypatch.setattr(database, 'get_definitions', lambda word: [])

    mock_message = AsyncMock()
    mock_message.text = "testword"
    mock_message.reply_text = AsyncMock()

    mock_update = MagicMock(spec=Update)
    mock_update.message = mock_message

    mock_context = MagicMock(spec=CallbackContext)

    await word_handler(mock_update, mock_context)

    mock_message.reply_text.assert_called_once_with(
        "Sanaa ei löytynyt"
    )

@pytest.mark.asyncio
async def test_word_handler_definition_found(monkeypatch):
    """
    Test message handler when definition(s) are found in database
    """
    mock_definitions = [
        (1, 'word', 'Word', 'Definition of word', 'Example of word usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),

        (2, 'word2', 'Word2', 'Definition of word2', 'Example of word2 usage',
         'User2', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
    ]

    expected_keyboard = InlineKeyboardMarkup([])
    expected_reply = "expected"

    monkeypatch.setattr(database, 'get_definitions', lambda word: mock_definitions)
    monkeypatch.setattr(bot, 'build_keyboard', lambda defs, index: expected_keyboard)
    monkeypatch.setattr(bot, 'build_reply', lambda text: expected_reply)

    mock_message = AsyncMock()
    mock_message.text = "word"
    mock_message.reply_text = AsyncMock()

    mock_update = MagicMock(spec=Update)
    mock_update.message = mock_message

    mock_context = MagicMock(spec=CallbackContext)

    await word_handler(mock_update, mock_context)

    mock_message.reply_text.assert_called_once_with(
        expected_reply,
        reply_markup=expected_keyboard,
        parse_mode=constants.ParseMode.HTML)

# Test callback handler
@pytest.mark.asyncio
async def test_callback_handler_none_callback():
    """
    Test callback handler when callback data is none
    """
    mock_query = AsyncMock(spec=CallbackQuery)
    mock_query.data = "none"
    mock_query.answer = AsyncMock()

    mock_update = AsyncMock(spec=Update, callback_query=mock_query)
    mock_context = AsyncMock(spec=CallbackContext)

    await callback_handler(mock_update, mock_context)

    mock_query.answer.assert_called_once()

    mock_query.edit_message_text.assert_not_called()


@pytest.mark.asyncio
async def test_callback_handler_invalid_callback():
    """
    Test callback handler when callback data is invalid
    """
    mock_query = AsyncMock(spec=CallbackQuery)
    mock_query.data = "invalid"
    mock_query.answer = AsyncMock()

    mock_update = AsyncMock(spec=Update, callback_query=mock_query)
    mock_context = AsyncMock(spec=CallbackContext)

    await callback_handler(mock_update, mock_context)

    mock_query.answer.assert_called_once()

    mock_query.edit_message_text.assert_called_once_with("Invalid callback data")

@pytest.mark.asyncio
async def test_callback_handler_no_definitions(monkeypatch):
    """
    Test callback handler behavior when no definitions found
    """
    monkeypatch.setattr(database, 'get_definitions', lambda word: [])
    mock_query = AsyncMock(spec=CallbackQuery)
    mock_query.data = "def:word:1"
    mock_query.answer = AsyncMock()

    mock_update = AsyncMock(spec=Update, callback_query=mock_query)
    mock_context = AsyncMock(spec=CallbackContext)

    await callback_handler(mock_update, mock_context)

    mock_query.answer.assert_called_once()

    mock_query.edit_message_text.assert_called_once_with("Sanaa ei löytynyt")

@pytest.mark.asyncio
async def test_callback_handler_valid_definitions(monkeypatch):
    """
    Test callback handler behavior when valid definitions are found
    """
    mock_definitions = [
        (1, 'word', 'Word', 'Definition of word', 'Example of word usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),

        (2, 'word', 'Word', 'Definition of word2', 'Example of word2 usage',
         'User2', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
    ]
    monkeypatch.setattr(database, 'get_definitions', lambda word: mock_definitions)

    mock_query = AsyncMock(spec=CallbackQuery)
    mock_query.data = "def:word:1"
    mock_query.answer = AsyncMock()

    mock_update = AsyncMock(spec=Update, callback_query=mock_query)
    mock_context = AsyncMock(spec=CallbackContext)

    expected_reply = "expected"
    mock_build_reply = MagicMock(return_value=expected_reply)

    expected_keyboard = InlineKeyboardMarkup([])
    mock_build_keyboard = MagicMock(return_value=expected_keyboard)

    monkeypatch.setattr("bot.build_reply", mock_build_reply)
    monkeypatch.setattr("bot.build_keyboard", mock_build_keyboard)

    await callback_handler(mock_update, mock_context)

    mock_query.answer.assert_called_once()

    mock_build_reply.assert_called_once_with(mock_definitions[1])
    mock_build_keyboard.assert_called_once_with(mock_definitions, 1)

    mock_query.edit_message_text.assert_called_once_with(
        expected_reply,
        reply_markup=expected_keyboard,
        parse_mode=constants.ParseMode.HTML
    )

# Test inline query
@pytest.mark.asyncio
async def test_inline_query_empty():
    """
    Test behavior of inline queries when query is empty
    """
    mock_inline_query = AsyncMock(spec=InlineQuery)
    mock_inline_query.query = ""
    mock_update = AsyncMock(spec=Update, inline_query=mock_inline_query)
    mock_context = AsyncMock(spec=CallbackContext)

    await inline_query(mock_update, mock_context)

    mock_update.inline_query.answer.assert_not_called()

@pytest.mark.asyncio
async def test_inline_query_no_definitions(monkeypatch):
    """
    Test inline query behavior when no definitions are found
    """
    mock_get_definitions = MagicMock(return_value=[])
    monkeypatch.setattr(database, "get_definitions", mock_get_definitions)
    mock_inline_query = AsyncMock(spec=InlineQuery)
    mock_inline_query.query = "invalid_invalid"

    mock_update = AsyncMock(spec=Update, inline_query=mock_inline_query)
    mock_context = AsyncMock(spec=CallbackContext)

    await inline_query(mock_update, mock_context)

    mock_get_definitions.assert_called_once_with("invalid_invalid")
    mock_update.inline_query.answer.assert_called_once()

    results = mock_update.inline_query.answer.call_args[0][0]
    assert len(results) == 1
    assert isinstance(results[0], InlineQueryResultArticle)
    assert results[0].title == "Ei tuloksia"
    assert "Selityksiä ei löytynyt" in results[0].input_message_content.message_text

@pytest.mark.asyncio
async def test_inline_query_valid_definitions(monkeypatch):
    """
    Test inline query behavior when definitions are found
    """
    mock_definitions = [
        (1, 'word', 'Word', 'Definition of word', 'Example of word usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),

        (2, 'word', 'Word', 'Definition of word2', 'Example of word2 usage',
         'User2', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
    ]
    mock_get_definitions = MagicMock(return_value=mock_definitions)
    monkeypatch.setattr(database, "get_definitions", mock_get_definitions)
    mock_inline_query = AsyncMock(spec=InlineQuery)
    mock_inline_query.query = "word"

    mock_update = AsyncMock(spec=Update, inline_query=mock_inline_query)
    mock_context = AsyncMock(spec=CallbackContext)

    await inline_query(mock_update, mock_context)

    mock_get_definitions.assert_called_once_with("word")
    mock_update.inline_query.answer.assert_called_once()

    results = mock_update.inline_query.answer.call_args[0][0]
    assert len(results) == 2
    assert isinstance(results[0], InlineQueryResultArticle)
    assert results[0].title == "Selitys #1"
    assert "Käyttäjältä: User | <i>Postattu dd.mm.yyyy</i>" in results[0].input_message_content.message_text # pylint: disable=C0301

def test_get_application_handlers():
    """
    Test return correct handlers
    """
    results = get_application_handlers()
    assert len(results) == 4
    assert isinstance(results[0], CommandHandler)
    assert isinstance(results[1], MessageHandler)
    assert isinstance(results[2], CallbackQueryHandler)
    assert isinstance(results[3], InlineQueryHandler)
