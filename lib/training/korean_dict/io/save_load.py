import sqlite3
from collections import Counter
from pathlib import Path
from typing import Dict
import json

from lib import paths
from lib.training.omen.evaluate_password import calc_omen_keyspace, find_omen_level
from lib.training.omen.omen_parser import AlphabetGrammar
from lib.training.io.omen_train_data_output import save_omen_to_sqlite

from wordfreq import top_n_list

from lib.training.util.korean import hangul2dubeol, hangul2roman

DB_PATH = paths.KOREAN_DICT_DB_PATH
VALID_WORDS = set(top_n_list("en", n=5000))

def caculate_prob_and_save_to_db():

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT word, count FROM FilteredKoreanDict")
    rows = cursor.fetchall()
    conn.close()

    loan_word_set = load_loan_word()

    dubeol_ctr = Counter()
    omen = AlphabetGrammar(
        ngram=2,
        max_length=20,
        min_length=0
    )
    for w, cnt in rows:
        omen.parse(w,cnt)
        try:
            k = hangul2dubeol(w)
            for roman in hangul2roman(w):
                if roman in loan_word_set:
                    print(f"[Warning] loan word '{roman}' is used in '{w}'")
                    continue
                if roman in VALID_WORDS:
                    print(f"[Warning] valid english word '{roman}' is used in '{w}'")
                    continue
                if roman and len(roman) > 2:
                    dubeol_ctr[roman] += cnt
            if k and len(k) > 2:
                dubeol_ctr[k] += cnt
        except Exception as e:
            print(f"[Warning] romanization failed for '{w}': {e}")
    omen.apply_smoothing()

    keyspace = calc_omen_keyspace(omen)
    levels = Counter()

    for w, cnt in rows:
        levels[find_omen_level(omen, w)] += 1

    program_info = {
        "ngram": 2,
        "encoding": "utf-8",
        "alphabet": "".join(chr(c) for c in range(ord("가"), ord("힣") + 1))
    }

    save_omen_to_sqlite(omen, keyspace, levels, len(rows),DB_PATH, program_info)

    V = len(dubeol_ctr)
    T = sum(dubeol_ctr.values())
    word_probs = {
        token: (count + 1) / (T + V)
        for token, count in dubeol_ctr.items()
    }

    save_word_probs_to_sqlite(word_probs)

def load_loan_word():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM LoanwordDict")
    rows = cursor.fetchall()
    loan_word_set = set()
    for row in rows:
        loan_word_set.add(row[2].lower())
    conn.close()
    return loan_word_set


def save_word_probs_to_sqlite(word_probs: Dict[str, float]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS UnigramProbs")
    cursor.execute("CREATE TABLE UnigramProbs (token TEXT PRIMARY KEY, probability REAL)")

    cursor.executemany(
        "INSERT INTO UnigramProbs (token, probability) VALUES (?, ?)",
        word_probs.items()
    )

    conn.commit()
    conn.close()

def load_checkpoint_counts(path: str) -> Counter:
    path = Path(path)
    if not path.exists():
        return Counter()
    items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        return Counter(items)
    return Counter({w: cnt for w, cnt in items})


def load_checkpoint_done(path: Path) -> set:
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def save_checkpoint_counts(counter: Counter, path: Path):
    items = counter.most_common()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def save_checkpoint_done(done: set, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(done), ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    caculate_prob_and_save_to_db()
