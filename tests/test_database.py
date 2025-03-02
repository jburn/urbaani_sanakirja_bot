# pylint: disable=redefined-outer-name
"""
Tests for the word_database module
"""
import sqlite3
import pytest
from word_database import WordDatabase

@pytest.fixture
def test_db():
    """
    Create test version of WordDatabase
    """
    db = WordDatabase(":memory:") # create in-memory db
    conn = db.conn
    cursor = db.cursor

    cursor.executemany("""
            INSERT INTO words (word, title, explanation, examples, user, date, likes, dislikes, labels)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ('word', 'Word', 'Definition of word', 'Example of word usage',
                 'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
                ('word', 'Word2', 'Definition of word2', 'Example of word2 usage',
                 'User2', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
                ('test', 'test', 'Definition of test', 'Example of test usage',
                 'User2', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)')
            ]
    )
    conn.commit()
    yield db
    conn.close()

def test_insert_definition_successful(test_db):
    """
    Test if inserting a valid word into database works
    """
    result = test_db.insert_definition(
        ('word3', 'Word3', 'Definition of word3', 'Example of word3 usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'))
    assert result is True
    assert len(test_db.get_definitions('word3')) == 1

def test_insert_definition_exists(test_db):
    """
    Test if inserting an existing definition returns false
    """
    result = test_db.insert_definition(
        ('word', 'Word', 'Definition of word', 'Example of word usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'))
    assert result is False

def test_insert_definition_error(test_db):
    """
    Test if inserting invalid word object returns false
    """
    result = test_db.insert_definition(
        ('', None, 'Definition of word', 'Example of word usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'))
    assert result is False

def test_delete_duplicates(test_db):
    """
    Test if deleting duplicates works
    """
    test_db.cursor.execute("""
        INSERT INTO words (word, title, explanation, examples, user, date, likes, dislikes, labels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ('word', 'Word2', 'Definition of word', 'Example of word usage',
         'User', 'dd.mm.yyyy', '10', '10', 'Label2 (1), Label1 (1)'),
    )
    assert len(test_db.get_all_definitions()) == 4
    test_db.delete_duplicates()
    assert len(test_db.get_all_definitions()) == 3

def test_get_all_definitions(test_db):
    """
    Test that getting all definitions works
    """
    results = test_db.get_all_definitions()
    assert len(results) == 3

def test_get_definitions_found(test_db):
    """
    Test that getting definitions for a certain word works
    """
    results = test_db.get_definitions('word')
    assert len(results) == 2
    assert results[0][2] == "Word"
    assert results[1][2] == "Word2"

def test_get_definitions_not_found(test_db):
    """
    Test that definition not found behaves correctly
    """
    results = test_db.get_definitions('not_found')
    assert len(results) == 0

def test_close(test_db):
    """
    Test that database closing works correctly
    """
    test_db.close()
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        cursor = test_db.cursor
        cursor.execute("SELECT 1")
