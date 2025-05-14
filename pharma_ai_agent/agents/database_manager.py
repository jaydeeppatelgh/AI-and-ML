import sqlite3

class DatabaseManager:
    def __init__(self, db_name='leads.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS leads (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT,
                                address TEXT,
                                needs TEXT,
                                contacted BOOLEAN)''')
        self.conn.commit()

    def save_lead(self, lead):
        self.cursor.execute('''INSERT INTO leads (name, address, needs, contacted)
                               VALUES (?, ?, ?, ?)''', 
                               (lead['name'], lead['address'], ', '.join(lead['needs']), False))
        self.conn.commit()

    def get_pending_leads(self):
        self.cursor.execute('SELECT * FROM leads WHERE contacted = 0')
        return self.cursor.fetchall()
