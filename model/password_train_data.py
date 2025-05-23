import sqlite3

import Constants


class PasswordTrainData:
    def __init__(self, db_name=Constants.BASE_PATH+'sqlite3.db'):
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()
        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS password_train_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT
        )
        ''')

    def add_password(self, email, password):
        self.cur.execute('''
        INSERT INTO password_train_data (email, password) VALUES (?, ?)
        ''', (email, password))
        self.conn.commit()

    def add_passwords(self,passwords):
        self.cur.executemany('''
        INSERT INTO password_train_data (email, password) VALUES (?, ?)
        ''', passwords)
        self.conn.commit()

    def find_all_password(self, chunk_size=100):
        self.cur.execute('SELECT * FROM password_train_data')
        while True:
            rows = self.cur.fetchmany(chunk_size)
            if not rows:
                break
            for row in rows:
                yield row

    def close(self):
        self.conn.close()