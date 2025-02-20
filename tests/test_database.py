import pytest
from unittest.mock import MagicMock
from word_database import WordDatabase

@pytest.fixture
def mock_database():
    """
    Create mock version of WordDatabase
    """
    db = WordDatabase()
    db.connect = MagicMock()
    return db

