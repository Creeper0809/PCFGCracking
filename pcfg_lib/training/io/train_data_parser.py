# File: pcfg_lib/training/io/train_data_parser.py
import sqlite3
from typing import Iterator

class TrainingDataParser:
    def __init__(self, min_length: int, max_length: int, filedir: str, encoding: str = "utf-8"):
        self.min_length = min_length
        self.max_length = max_length
        self.encoding = encoding
        self.filedir = filedir
        self.num_passwords = 0
        self.table_name = 'password_train_data_filtered'
        if filedir.lower().endswith('.db'):
            self._mode = 'db'
            self._conn = sqlite3.connect(filedir)
            self._cur = self._conn.cursor()
        else:
            self._mode = 'txt'
            self._file_path = filedir

    def check_valid(self, pwd: str) -> bool:
        if not (self.min_length <= len(pwd) <= self.max_length):
            return False
        if "\t" in pwd:
            return False
        for code in range(0x20):
            if chr(code) in pwd:
                return False
        if '\u2028' in pwd or '\u0085' in pwd:
            return False
        return True

    def count_passwords(self) -> int:
        if self._mode == 'db':
            self._cur.execute(f'SELECT COUNT(*) FROM {self.table_name}')
            return self._cur.fetchone()[0]
        count = 0
        with open(self._file_path, 'r', encoding=self.encoding) as f:
            for line in f:
                pwd = line.rstrip('\r\n')
                if pwd.startswith('$HEX[') and pwd.endswith(']'):
                    try:
                        pwd = bytes.fromhex(pwd[5:-1]).decode(self.encoding)
                    except:
                        continue
                try:
                    pwd.encode(self.encoding)
                except UnicodeEncodeError:
                    continue
                if self.check_valid(pwd):
                    count += 1
        return count

    def read_password(self) -> Iterator[str]:
        if self._mode == 'db':
            self._cur.execute(f'SELECT password FROM {self.table_name}')
            for (pwd,) in self._cur:
                self.num_passwords += 1
                if self.check_valid(pwd):
                    yield pwd
        else:
            with open(self._file_path, 'r', encoding=self.encoding) as f:
                for line in f:
                    self.num_passwords += 1
                    pwd = line.rstrip('\r\n')
                    if pwd.startswith('$HEX[') and pwd.endswith(']'):
                        try:
                            pwd = bytes.fromhex(pwd[5:-1]).decode(self.encoding)
                        except:
                            continue
                    try:
                        pwd.encode(self.encoding)
                    except UnicodeEncodeError:
                        continue
                    if self.check_valid(pwd):
                        yield pwd
    def close(self):
        if self._mode == 'db':
            self._conn.close()