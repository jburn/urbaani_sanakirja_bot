import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update
from telegram.ext import CallbackContext
from bot import *

# import bot for mock monkeypatching
import bot


# Test helper functions
# Test build reply
@pytest.mark.parametrize(
    "word, expected_reply",
    [
        # Word with examples (should return reply with examples)
        (
            (1, 'word', 'Word', 'Definition of word', 'Example of word usage', 'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
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
            (1, 'word', 'Word', 'Definition of word', '', 'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
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
        f'Moro {mock_user.first_name}! Lähetä minulle jokin sana, niin yritän etsiä sille selityksen.'
    )

@pytest.mark.asyncio
async def test_word_handler_no_definition_found(monkeypatch):
    """
    Test message handler when no definitions are found in database
    """
    monkeypatch.setattr(database, 'get_definitions', lambda text: [])

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
        (1, 'word', 'Word', 'Definition of word', 'Example of word usage', 'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
        (2, 'word2', 'Word2', 'Definition of word2', 'Example of word2 usage', 'User2', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
    ]

    expected_keyboard = InlineKeyboardMarkup([])
    expected_reply = "expected"

    monkeypatch.setattr(database, 'get_definitions', lambda text: mock_definitions)
    monkeypatch.setattr(bot, 'build_keyboard', lambda defs, index: expected_keyboard)
    monkeypatch.setattr(bot, 'build_reply', lambda text: expected_reply)

    mock_message = AsyncMock()
    mock_message.text = "word"
    mock_message.reply_text = AsyncMock()

    mock_update = MagicMock(spec=Update)
    mock_update.message = mock_message
    
    mock_context = MagicMock(spec=CallbackContext)

    await word_handler(mock_update, mock_context)
    
    mock_message.reply_text.assert_called_once_with(expected_reply, reply_markup=expected_keyboard, parse_mode=constants.ParseMode.HTML)
