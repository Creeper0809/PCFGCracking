import sqlite3
from collections import Counter

def save_omen_to_sqlite(
    alphabet_grammar,
    omen_keyspace,
    omen_levels_count,
    num_valid_passwords,
    db_path,
    program_info
):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 1. 접두사
        c.execute("DROP TABLE IF EXISTS PrefixLevel")
        c.execute("CREATE TABLE PrefixLevel (prefix TEXT PRIMARY KEY, level INTEGER)")
        c.executemany("INSERT INTO PrefixLevel VALUES (?, ?)", [
            (prefix, node.start_level)
            for prefix, node in alphabet_grammar.grammar.items()
        ])

        # 2. 접미사
        c.execute("DROP TABLE IF EXISTS SuffixLevel")
        c.execute("CREATE TABLE SuffixLevel (prefix TEXT PRIMARY KEY, level INTEGER)")
        c.executemany("INSERT INTO SuffixLevel VALUES (?, ?)", [
            (prefix, node.end_level)
            for prefix, node in alphabet_grammar.grammar.items()
        ])

        # 3. 조건부 확률
        c.execute("DROP TABLE IF EXISTS ConditionalProb")
        c.execute("CREATE TABLE ConditionalProb (token TEXT PRIMARY KEY, level INTEGER)")
        data = []
        for prefix, node in alphabet_grammar.grammar.items():
            for next_char, level_info in node.next_letter_candidates.items():
                level = level_info[0] if isinstance(level_info, (list, tuple)) else level_info
                data.append((prefix + next_char, level))
        c.executemany("INSERT INTO ConditionalProb VALUES (?, ?)", data)

        # 4. 길이 기반 레벨
        c.execute("DROP TABLE IF EXISTS LengthLevel")
        c.execute("CREATE TABLE LengthLevel (level INTEGER)")
        c.executemany("INSERT INTO LengthLevel VALUES (?)", [
            (entry[0] if isinstance(entry, (list, tuple)) else entry,)
            for entry in alphabet_grammar.ln_lookup
        ])

        # 5. 설정 정보 (ngram, encoding)
        c.execute("DROP TABLE IF EXISTS Config")
        c.execute("CREATE TABLE Config (key TEXT PRIMARY KEY, value TEXT)")
        c.executemany("INSERT INTO Config VALUES (?, ?)", [
            ("ngram", str(program_info["ngram"])),
            ("encoding", program_info["encoding"]),
        ])

        # 6. 알파벳
        c.execute("DROP TABLE IF EXISTS Alphabet")
        c.execute("CREATE TABLE Alphabet (ch TEXT PRIMARY KEY)")
        c.executemany("INSERT INTO Alphabet VALUES (?)", [(ch,) for ch in program_info["alphabet"]])

        # 7. omen_keyspace
        c.execute("DROP TABLE IF EXISTS OmenKeyspace")
        c.execute("CREATE TABLE OmenKeyspace (level INTEGER PRIMARY KEY, keyspace INTEGER)")
        c.executemany("INSERT INTO OmenKeyspace VALUES (?, ?)", omen_keyspace.items())

        # 8. 크랙된 비밀번호 수
        c.execute("DROP TABLE IF EXISTS PasswordsPerLevel")
        c.execute("CREATE TABLE PasswordsPerLevel (level INTEGER PRIMARY KEY, count INTEGER)")
        c.executemany("INSERT INTO PasswordsPerLevel VALUES (?, ?)", omen_levels_count.items())

        # 9. 추정 확률 계산
        c.execute("DROP TABLE IF EXISTS PcfgOmenProb")
        c.execute("CREATE TABLE PcfgOmenProb (level INTEGER PRIMARY KEY, probability REAL)")
        pcfg_omen_prob = Counter()
        for lvl, ks in omen_keyspace.items():
            if ks == 0:
                continue
            num_inst = omen_levels_count.get(lvl, 0)
            pct = num_inst / num_valid_passwords
            pcfg_omen_prob[lvl] = pct / ks
        c.executemany("INSERT INTO PcfgOmenProb VALUES (?, ?)", pcfg_omen_prob.items())

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[에러] OMEN 데이터 SQLite 저장 실패 → {e}")
        return False
