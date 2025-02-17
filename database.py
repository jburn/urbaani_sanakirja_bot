import sqlite3
import json

def init_db():
    con = sqlite3.connect("words.db")
    cur = con.cursor()
    cur.execute("CREATE table word(id, word, title, explanation, examples, user, date, likes, dislikes, labels)")
    con.commit()
    con.close()

def get_definitions(word):
    word = word.lower().strip()
    con = sqlite3.connect("words.db")
    cur = con.cursor()
    cur.execute(f"SELECT * FROM word WHERE word='{word}'")
    return cur.fetchall()

if __name__ == "__main__":
    try:
        init_db()
    except:
        pass

    con = sqlite3.connect("words.db")
    cur = con.cursor()

    with open("new_defs.json", "r", encoding="utf-8") as rfile:
        data = json.load(rfile)
    obj = []
    id = 0
    for word in data.keys():
        title = data[word]["title"]
        for definition in data[word]["list"]:
            explanation = definition["explanation"]
            examples = "\n\n".join(definition["examples"])
            user = definition["user"]
            date = definition["date"]
            likes = definition["upvotes"]
            dislikes = definition["downvotes"]
            labels = definition["labels"]
            obj.append((id, word, title, explanation, examples, user, date, likes, dislikes, str(labels)))
            id += 1

    con.executemany("INSERT INTO word VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", obj)

    con.commit()

    #for row in con.execute("SELECT * FROM word WHERE word = 'flexaa'"):
    #    print(row[2], row[3])
    #    input()
    #