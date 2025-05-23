import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Dict
import json

import Constants
from korean_dict.util.han2en import hangul_to_romanization, hangul_to_dubeolsik

DB_PATH = os.path.join(Constants.BASE_PATH, "sqlite3.db")

def caculate_prob_and_save_to_db():
    final_items = load_checkpoint_counts(os.path.join(Constants.KOREAN_DICT_PATH, "korean_dict_filtered.json"))
    dubeol_ctr = Counter()

    for w, cnt in final_items.items():
        k = hangul_to_dubeolsik(w)
        try:
            for i in hangul_to_romanization(w):
                if i and len(i) > 2:
                    dubeol_ctr[i] += cnt
        except Exception as e:
            print(f"[Warning] romanization failed for '{w}': {e}")
        if k and len(k) > 2:
            dubeol_ctr[k] += cnt

    V = len(dubeol_ctr)
    T = sum(dubeol_ctr.values())

    word_probs = {
        token: (count + 1) / (T + V)
        for token, count in dubeol_ctr.items()
    }

    save_word_probs_to_sqlite(word_probs)


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


def load_word_probs_from_sqlite() -> Dict[str, float]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT token, probability FROM UnigramProbs")
    rows = cursor.fetchall()
    conn.close()
    return {token: prob for token, prob in rows}


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
