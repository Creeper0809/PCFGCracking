import sqlite3
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Iterable

from pcfg_lib.training.detectors.korean_detection import segment_word  # noqa: F401 (implicit import for workers)
from pcfg_lib.training.pcfg.pcfg_parser import PCFGParser
from pcfg_lib.training.pcfg.word_trie import WordTrie

EMAIL_DOMAINS_SKIP = ("naver.com", "hanmail.com")
BATCH_SIZE = 1000

_parser: PCFGParser | None = None


def _init_worker() -> None:
    global _parser
    _parser = PCFGParser(WordTrie(needed_appear=5))


def _keep(email: str, pwd: str) -> bool:
    if email.endswith(EMAIL_DOMAINS_SKIP):
        return True
    for segment in _parser.parse(pwd):
        print(segment)
        if any(lbl and lbl.startswith("H") for _, lbl in segment):
            return True
        if any(lbl and lbl.startswith("A") for _, lbl in segment):
            return False
    return True

def _process_batch(batch: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    return [(e, p) for e, p in batch if _keep(e, p)]


def _chunked(data: List[Tuple[str, str]], size: int) -> Iterable[List[Tuple[str, str]]]:
    for i in range(0, len(data), size):
        yield data[i : i + size]


def main(db_path: str = "../sqlite3.db", n_workers: int = 8):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT email, password FROM password_train_data")
    rows = cur.fetchall()

    results = []
    with ProcessPoolExecutor(max_workers=n_workers, initializer=_init_worker) as pool:
        for kept in pool.map(_process_batch, _chunked(rows, BATCH_SIZE)):
            results.extend(kept)

    cur.executescript(
        """
        DROP TABLE IF EXISTS password_train_data_filtered;
        CREATE TABLE IF NOT EXISTS password_train_data_filtered (
            email TEXT,
            password TEXT
        );
        """
    )
    cur.executemany(
        "INSERT INTO password_train_data_filtered(email, password) VALUES (?, ?)",
        results,
    )
    con.commit()
    con.close()


if __name__ == "__main__":
    main()