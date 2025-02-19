import sqlite3

class WordDatabase:
    def __init__(self, name='words.db'):
        self.name = name
        self.conn = sqlite3.connect(self.name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
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
        self.cursor.execute('''DELETE FROM words
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM words
            GROUP BY word, explanation
        );''')
        self.conn.commit()

    def definition_exists(self, word, explanation):
        word_lower = word.lower()
        self.cursor.execute('SELECT 1 FROM words WHERE word = ? AND explanation = ?', (word_lower, explanation))
        return self.cursor.fetchone() is not None

    def insert_definition(self, word: str, title:str, explanation:str, examples:str, user:str, date:str, likes:str, dislikes:str, labels:str):
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
        
    def get_all_definitions(self):
        self.cursor.execute('SELECT * from words')
        return self.cursor.fetchall()

    def get_definitions(self, word):
        word_lower = word.lower()
        self.cursor.execute('SELECT * FROM words WHERE word = ?', (word_lower,))
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()