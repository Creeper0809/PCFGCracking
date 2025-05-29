import sqlite3
from collections import Counter

def _calculate_probabilities(counter: Counter) -> list[tuple]:
    total = sum(counter.values())
    if total == 0:
        return []
    return [(item, count / total) for item, count in counter.items()]

def save_counter_to_db(conn, table_name: str, counter_map: dict):
    try:
        c = conn.cursor()
        c.execute(f"DROP TABLE IF EXISTS {table_name}")
        c.execute(f"CREATE TABLE {table_name} (length TEXT, item TEXT, probability REAL)")

        for idx, counter in counter_map.items():
            prob_list = _calculate_probabilities(counter)
            c.executemany(
                f"INSERT INTO {table_name} (length, item, probability) VALUES (?, ?, ?)",
                [(str(idx), item, prob) for item, prob in prob_list]
            )

        conn.commit()
        return True
    except Exception as e:
        print(f"[에러] 테이블 저장 실패: {table_name} → {e}")
        return False

def save_pcfg_to_sqlite(db_path, pcfg_parser):
    try:
        conn = sqlite3.connect(db_path)

        mappings = [
            ("Keyboard",       pcfg_parser.count_keyboard),
            ("Years",          {'1': pcfg_parser.count_years}),
            ("Alpha",          pcfg_parser.count_alpha),
            ("Capitalization", pcfg_parser.count_alpha_masks),
            ("Digits",         pcfg_parser.count_digits),
            ("Special",        pcfg_parser.count_special),
            ("Korean",         pcfg_parser.count_korean),
            ("Grammar",        {'grammar': pcfg_parser.count_base_structures}),
            ("Prince",         {'grammar': pcfg_parser.count_prince}),
        ]

        for table_name, counter_map in mappings:
            if not save_counter_to_db(conn, table_name, counter_map):
                print(f"[에러] '{table_name}' 테이블 저장 실패")
                return False

        conn.close()
        return True
    except Exception as e:
        print(f"[에러] 데이터베이스 저장 실패 → {e}")
        return False
