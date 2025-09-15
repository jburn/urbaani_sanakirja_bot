"""
Class for interacting with the word dictionary database
"""
import sqlite3
import dotenv
import os

class WordDatabase:
    """
    Database class for interacting with the word database
    """
    def __init__(self, name='words.db'):
        dotenv.load_dotenv()
        word_db = os.getenv("WORD_DATABASE")
        if not word_db:
            self.name = name
        else:
            self.name = word_db
        self.conn = sqlite3.connect(self.name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """
        Create table for storing word definitions
        """
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS words(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            title TEXT NOT NULL,
            explanation TEXT,
            examples TEXT,
            user TEXT,
            date TEXT,
            likes TEXT,
            dislikes TEXT,
            labels TEXT)
        ''')
        self.conn.commit()

    def delete_duplicates(self):
        """
        Delete duplicate definitions from database
        """
        self.cursor.execute('''
        DELETE FROM words WHERE id NOT IN (
            SELECT MIN(id)
            FROM words
            GROUP BY word, explanation
        );
        ''')
        self.conn.commit()

    def definition_exists(self, word: str, explanation: str) -> bool:
        """
        Check if a duplicate definition exists in the database¨

        returns: True if duplicate exists, False if does not
        """
        word_lower = word.lower()
        self.cursor.execute(
            'SELECT 1 FROM words WHERE word = ? AND explanation = ?',
            (word_lower, explanation)
            )
        return self.cursor.fetchone() is not None

    def insert_definition(self, word_obj: tuple) -> bool:
        """
        Insert a new definition into the database

        returns: boolean indicating if the operation was a success
        """
        word, title, explanation, examples, user, date, likes, dislikes, labels = word_obj
        if self.definition_exists(word, explanation):
            return False
        try:
            self.cursor.execute('''
                INSERT INTO words (word, title, explanation, examples, user, date, likes, dislikes, labels)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (word, title, explanation, examples, user, date, likes, dislikes, labels))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error when inserting into database: {e}")
            return False

    def get_all_definitions(self) -> list:
        """
        Return all database entries for words

        returns: all definitions from the database
        """
        self.cursor.execute('SELECT * from words')
        return self.cursor.fetchall()

    def get_definitions(self, word: str) -> list:
        """
        Get definitions for word

        returns: list of tuples containing word definitions
        """
        word_lower = word.lower()
        self.cursor.execute('SELECT * FROM words WHERE word = ?', (word_lower,))
        return self.cursor.fetchall()

    def close(self):
        """
        Close database connection
        """
        self.conn.close()
