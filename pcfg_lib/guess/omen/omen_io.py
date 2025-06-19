import sqlite3

def load_omen_rules(db_path):
    print(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Config
    c.execute("SELECT key, value FROM Config")
    program_info = {}
    for key, value in c.fetchall():
        if key == "ngram":
            program_info["ngram"] = int(value)
        elif key == "encoding":
            program_info["encoding"] = value

    # Alphabet
    c.execute("SELECT ch FROM Alphabet")
    alphabet = [row[0] for row in c.fetchall()]
    program_info["alphabet"] = alphabet

    # Grammar
    grammar = {
        "alphabet": alphabet,
        "alphabet_encoding": program_info["encoding"],
        "ngram": program_info["ngram"]
    }

    # IP
    rows = c.execute("SELECT prefix, level FROM PrefixLevel").fetchall()
    max_level = max(level for _, level in rows)
    grammar["max_level"] = max_level
    grammar["ip"] = {i: [] for i in range(max_level + 1)}
    for prefix, level in rows:
        grammar["ip"][level].append(prefix)

    grammar["ep"] = {
        prefix: level
        for prefix, level in c.execute("SELECT prefix, level FROM SuffixLevel")
    }

    grammar["cp"] = {}
    for token, level in c.execute("SELECT token, level FROM ConditionalProb"):
        prefix, ch = token[:-1], token[-1]
        grammar["cp"].setdefault(prefix, {}).setdefault(level, []).append(ch)

    ln_rows = [r[0] for r in c.execute("SELECT level FROM LengthLevel ORDER BY rowid")]
    min_size = grammar["ngram"]
    grammar["ln"] = {i: [] for i in range(max_level + 1)}
    for idx, cp_count in enumerate(ln_rows):
        length = idx + min_size
        grammar["ln"][cp_count].append(length)

    omen_keyspace = {
        level: keyspace
        for level, keyspace in c.execute("SELECT level, keyspace FROM OmenKeyspace")
    }

    grammar["omen_keyspace"] = omen_keyspace

    omen_levels_count = {
        level: count
        for level, count in c.execute("SELECT level, count FROM PasswordsPerLevel")
    }

    grammar["omen_levels_count"] = omen_levels_count

    conn.close()
    return grammar

def load_omen_prob(dbpath,grammar):
    from pcfg_lib.guess.pcfg.pcfg_guesser import Type
    conn = sqlite3.connect(dbpath)
    curser = conn.cursor()

    curser.execute("SELECT level, probability FROM PcfgOmenProb")
    data = {}
    for level, prob in curser.fetchall():
        data[level] = {Type.PROB: prob, Type.TERMINALS:[level]}

    grammar["M"] = data