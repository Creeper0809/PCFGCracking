import json
import os
import re
import sqlite3
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple

from lib import paths
from lib.training.korean_dict.data_parser.korean_copus_parser import KoreanCopusParser, YoutubeCommentParser
from lib.training.korean_dict.data_parser.name_parser import NameListParser
from lib.training.korean_dict.data_parser.new_word_parser import NewWordParser, NewWordParser2, NewWordParser3
from lib.training.korean_dict.data_parser.word_parser import TabularNounParser
from lib.training.korean_dict.io.save_load import load_checkpoint_counts, save_checkpoint_counts, save_checkpoint_done, \
    load_checkpoint_done

RE_HANGUL_SEQ = re.compile(r"[가-힣]+")

def assign_parsers(base):
    assignments = []
    for p in (base / "신조어단어리스트2").rglob("*.json"):
        assignments.append((p, NewWordParser3()))
    for p in (base / "유튜브댓글").rglob("*.json"):
        assignments.append((p, YoutubeCommentParser()))
    for p in (base / "신조어단어리스트").rglob("*.json"):
        assignments.append((p, NewWordParser()))
    for p in (base / "신조어코퍼스").rglob("*.json"):
        assignments.append((p, NewWordParser2()))
    for p in (base / "한글코퍼스").rglob("*.json"):
        assignments.append((p, KoreanCopusParser()))
    for p in (base / "이름리스트").rglob("*.csv"):
        assignments.append((p, NameListParser()))
    for p in (base / "한국어어휘단어리스트").rglob("*.txt"):
        assignments.append((p, TabularNounParser()))
    return assignments

def process_with(item) -> Counter:
    path, parser = item
    if isinstance(parser, (NameListParser, TabularNounParser)):
        return parser.parse(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return parser.parse(data)

def print_progress(completed, total, path_name, chunk_ctr, total_ctr, report_top, cols):
    print(f"[{completed}/{total}] {path_name}  "
          f"file_tokens={sum(chunk_ctr.values())}  "
          f"total_tokens={sum(total_ctr.values())}")
    topn = total_ctr.most_common(report_top)
    rows = (len(topn) + cols - 1) // cols
    for r in range(rows):
        line = []
        for c in range(cols):
            idx = r + c * rows
            if idx < len(topn):
                w, cnt = topn[idx]
                line.append(f"{w:<8}{cnt:6d}")
        print("   ".join(line))
    print("-" * 40)

def parallel_process_resume(assignments: List[Tuple[Path, object]],
                            checkpoint_counts: Path,
                            checkpoint_done: Path,
                            workers: int = 8,
                            report_top: int = 20,
                            cols: int = 5,
                            checkpoint_every: int = 10) -> Counter:
    total_ctr = load_checkpoint_counts(checkpoint_counts)
    done = load_checkpoint_done(checkpoint_done)
    todo = [item for item in assignments if item[0].name not in done]
    print(f"Checkpoint loaded: {len(done)} done, {len(todo)} needed")

    with ProcessPoolExecutor(workers) as exe:
        futures = {exe.submit(process_with, itm): itm for itm in todo}
        completed = 0
        for fut in as_completed(futures):
            path, _ = futures[fut]
            chunk = fut.result()
            total_ctr.update(chunk)
            done.add(path.name)
            completed += 1

            print_progress(
                completed=completed,
                total=len(todo),
                path_name=path.name,
                chunk_ctr=chunk,
                total_ctr=total_ctr,
                report_top=report_top,
                cols=cols
            )

            if completed % checkpoint_every == 0:
                save_checkpoint_counts(total_ctr, checkpoint_counts)
                save_checkpoint_done(done, checkpoint_done)

    save_checkpoint_counts(total_ctr, checkpoint_counts)
    save_checkpoint_done(done, checkpoint_done)
    return total_ctr

def save_counter_to_sqlite(counter: Counter, table_name: str):
    conn = sqlite3.connect(paths.KOREAN_DICT_DB_PATH)
    cur = conn.cursor()

    cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    cur.execute(f"CREATE TABLE {table_name} (word TEXT PRIMARY KEY, count INTEGER)")

    cur.executemany(
        f"INSERT INTO {table_name} (word, count) VALUES (?, ?)",
        counter.items()
    )

    conn.commit()
    conn.close()

def main():
    base = Path(r"D:\Progamming\dataset\korean_copus")
    assignments = assign_parsers(base)

    ck_counts = Path(os.path.join(paths.BASE_PATH, "checkpoint_counts.json"))
    ck_done = Path(os.path.join(paths.BASE_PATH, "checkpoint_done.json"))

    total_ctr = parallel_process_resume(
        assignments,
        checkpoint_counts=ck_counts,
        checkpoint_done=ck_done,
        workers=12,
        report_top=100,
        cols=5,
        checkpoint_every=10
    )

    save_counter_to_sqlite(total_ctr, table_name="RawKoreanDict")
    print("[INFO] Saved to sqlite3.db → table: RawKoreanDict")

if __name__ == "__main__":
    main()
