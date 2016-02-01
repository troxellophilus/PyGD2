import sqlite3

def build() {
    conn = sqlite3.connect('pygd2.db')
    c = conn.cursor()
    
    c.execute('DROP TABLE IF EXISTS players')
    c.execute('CREATE TABLE IF NOT EXISTS players(name TEXT PRIMARY KEY, id INTEGER)')
}
