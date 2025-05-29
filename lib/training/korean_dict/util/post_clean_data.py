import os
import re
import sqlite3
from collections import Counter

from lib import paths

_SUFFIX_RE = re.compile(r"^.+(?:합니다|습니다|는다고|으며|니까|하게|졌다|고요|하다|려고|지만"
                        r"|다는|니다|하고|해서|에도|는데|어요|어도|한데|리는|므로|히고|으로써|웠다|으면|찮)$")

RE_ONLY_HANGUL = re.compile(r'^[가-힣]{1,}$')
MEANINGFUL_SINGLE_CHAR = {
    "강", "불", "물", "눈", "빛", "힘", "맛", "별", "짱", "짤",
    "덕", "감", "일", "집", "방", "산", "띵", "팟", "흑", "헉",
    "금", "앗", "읍", "줄", "성", "장", "톡", "꿀", "움", "달"
}
CUSTOM_DICT = {
    "잼민": 100000
}

DB_PATH = os.path.join(paths.KOREAN_PATH, "korean_dict.db")

def load_raw_korean_dict_from_db() -> Counter:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT word, count FROM RawKoreanDict")
    rows = cur.fetchall()
    conn.close()
    return Counter(dict(rows))

def clean_and_save_to_sqlite():
    ctr = load_raw_korean_dict_from_db()

    filtered = Counter({
        w: cnt
        for w, cnt in ctr.items()
        if not _SUFFIX_RE.match(w)
        and RE_ONLY_HANGUL.fullmatch(w)
        and (len(w) > 1 or (len(w) == 1 and w in MEANINGFUL_SINGLE_CHAR))
    })

    filtered.update(CUSTOM_DICT)
    print(f"[INFO] Filtered {len(filtered)} words")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS FilteredKoreanDict")
    cur.execute("CREATE TABLE FilteredKoreanDict (word TEXT PRIMARY KEY, count INTEGER)")

    cur.executemany(
        "INSERT INTO FilteredKoreanDict (word, count) VALUES (?, ?)",
        filtered.items()
    )

    conn.commit()
    conn.close()
    print("[INFO] Saved to sqlite3.db → table: FilteredKoreanDict")

if __name__ == "__main__":
    clean_and_save_to_sqlite()
