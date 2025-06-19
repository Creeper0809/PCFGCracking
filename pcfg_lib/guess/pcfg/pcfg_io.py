import sqlite3
from collections import OrderedDict


def _load_terminal(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT length, item, probability FROM {table_name}")

    data = {}
    for idx, item, prob in cursor.fetchall():
        data.setdefault(idx, []).append((item, prob))
    return data


def load_pcfg_grammar(db_path):
    from pcfg_lib.guess.pcfg.pcfg_guesser import Type

    grammar = {}
    base_structures = []
    try:
        conn = sqlite3.connect(db_path)

        mappings = [
            ('Keyboard', 'K'),
            ('Years', 'Y'),
            ('Alpha', 'A'),
            ('Capitalization', 'C'),
            ('Digits', 'D'),
            ('Special', 'S'),
            ('Korean', 'H'),
        ]

        for table_name, prefix in mappings:
            try:
                data = _load_terminal(conn, table_name)
            except Exception as e:
                print(f"[경고] 테이블 '{table_name}' 로딩 실패 → {e}")
                continue

            for idx, items in data.items():
                name = prefix + str(idx)

                grouped = OrderedDict()
                for v, p in items:
                    grouped.setdefault(p, []).append(v)

                grammar[name] = [
                    {Type.TERMINALS: values, Type.PROB: prob,Type.LENGTHS: len(values)}
                    for prob, values in grouped.items()
                ]

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT item, probability FROM Grammar WHERE length = 'grammar'")
            rows = cursor.fetchall()

            for value, prob in rows:
                replacements = []
                token = ''
                for char in value:
                    if char.isalpha():
                        if token:
                            replacements.append(token)
                        token = char
                    else:
                        token += char
                if token:
                    replacements.append(token)

                i = 0
                while i < len(replacements):
                    if replacements[i].startswith('A') or replacements[i].startswith('H'):
                        length = replacements[i][1:]
                        replacements.insert(i + 1, 'C' + length)
                        i += 1
                    i += 1

                base_structures.append({
                    Type.PROB: prob,
                    Type.REPLACEMENTS: replacements
                })



        except Exception as e:
            print(f"[에러] Grammar 테이블 로딩 실패 → {e}")

        conn.close()

    except Exception as e:
        print(f"[에러] SQLite 파일 열기 실패 → {e}")
        return {}, []

    return grammar, base_structures