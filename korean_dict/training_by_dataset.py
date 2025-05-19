import json
import os
import re
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple

import Constants
from korean_dict.data_parser.korean_copus_parser import KoreanCopusParser, YoutubeCommentParser
from korean_dict.data_parser.name_parser import NameListParser
from korean_dict.data_parser.new_word_parser import NewWordParser, NewWordParser2, NewWordParser3
from korean_dict.data_parser.word_parser import TabularNounParser
from korean_dict.io.save_load import load_checkpoint_counts, save_checkpoint_counts, save_checkpoint_done, \
    load_checkpoint_done

RE_HANGUL_SEQ = re.compile(r"[가-힣]+")


def assign_parsers(base):
    assignments = []
    # 신조어리스트2
    for p in (base / "신조어단어리스트2").rglob("*.json"):
        assignments.append((p, NewWordParser3()))
    # 유튜브 댓글
    for p in (base / "유튜브댓글").rglob("*.json"):
        assignments.append((p, YoutubeCommentParser()))
    # 신조어 리스트 1 JSON
    for p in (base / "신조어단어리스트").rglob("*.json"):
        assignments.append((p, NewWordParser()))
    # 신조어 코퍼스 JSON
    for p in (base / "신조어코퍼스").rglob("*.json"):
        assignments.append((p, NewWordParser2()))
    # 한국어 코퍼스 JSON
    for p in (base / "한글코퍼스").rglob("*.json"):
        assignments.append((p, KoreanCopusParser()))
    # 이름 리스트 CSV
    for p in (base / "이름리스트").rglob("*.csv"):
        assignments.append((p, NameListParser()))
    # 명사 리스트
    for p in (base / "한국어어휘단어리스트").rglob("*.txt"):
        assignments.append((p, TabularNounParser()))

    return assignments


def process_with(item) -> Counter:
    path, parser = item

    if isinstance(parser, NameListParser) or isinstance(parser, TabularNounParser):
        return parser.parse(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    return parser.parse(data)


def print_progress(
        completed: int,
        total: int,
        path_name: str,
        chunk_ctr: Counter,
        total_ctr: Counter,
        report_top: int,
        cols: int
):
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


def parallel_process_resume(
        assignments: List[Tuple[Path, object]],
        checkpoint_counts: Path,
        checkpoint_done: Path,
        workers: int = 8,
        report_top: int = 20,
        cols: int = 5,
        checkpoint_every: int = 10
) -> Counter:
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


def main():
    base = Path(r"D:\Progamming\dataset\korean_copus")
    assignments = assign_parsers(base)

    ck_counts = Path(os.path.join(Constants.KOREAN_DICT_PATH,"checkpoint_counts.json"))
    ck_done = Path(os.path.join(Constants.KOREAN_DICT_PATH,"checkpoint_done.json"))

    total_ctr = parallel_process_resume(
        assignments,
        checkpoint_counts=ck_counts,
        checkpoint_done=ck_done,
        workers=12,
        report_top=100,
        cols=5,
        checkpoint_every=10
    )
    out = Path(os.path.join(Constants.KOREAN_DICT_PATH, "korean_dict.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(total_ctr, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
