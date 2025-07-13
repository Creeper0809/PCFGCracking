import os
import sqlite3
import string
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Iterable

from pcfg_lib import paths
from pcfg_lib.training.pcfg.pcfg_parser import PCFGParser
from pcfg_lib.training.pcfg.word_trie import WordTrie

EMAIL_DOMAINS_SKIP = ("naver.com", "hanmail.com")
BATCH_SIZE = 1000
N_WORKERS = 12

# ───── 싱글톤 파서 ─────
_parser = None
def get_parser() -> PCFGParser:
    global _parser
    if _parser is None:
        # 필요한 최소 등장 횟수 5인 WordTrie 로 파서 생성
        _parser = PCFGParser(WordTrie(needed_appear=5))
    return _parser

# ───── 필터링 함수 ─────
def _keep(email: str, pwd: str) -> bool:
    # 1) 특정 도메인은 무조건 유지
    if email.endswith(EMAIL_DOMAINS_SKIP):
        return True

    parser = get_parser()

    # 2) 이메일 세그먼트 검사
    email_segments = parser.parse(email)
    print("Email segments:", *email_segments)
    for segment in email_segments:
        # 'H'로 시작하는 라벨이 하나라도 있으면 즉시 유지
        if any(lbl and lbl.startswith("H") for _, lbl in segment):
            return True

    # 3) 비밀번호 세그먼트 검사
    pwd_segments = parser.parse(pwd)
    print("Password segments:", *pwd_segments)
    for segment in pwd_segments:
        if any(lbl and lbl.startswith("H") for _, lbl in segment):
            return True
    # 4) 어느 경우에도 H/A 라벨이 없으면 폐기
    return False


# ───── 배치 단위 처리 ─────
def _process_batch(batch: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    kept = []
    for email, pwd in batch:
        if _keep(email, pwd):
            kept.append((email, pwd))
    return kept

def _chunked(data: List[Tuple[str, str]], size: int) -> Iterable[List[Tuple[str, str]]]:
    it = iter(data)
    while True:
        chunk = list()
        try:
            for _ in range(size):
                chunk.append(next(it))
        except StopIteration:
            if chunk:
                yield chunk
            break
        yield chunk

# ───── 메인 ─────
def main(
    db_path: str = os.path.join(paths.ROOT_PATH, "password.db"),
    workers: int = N_WORKERS
):
    # 1) 기존 데이터 로드
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT email, password FROM password_train_data")
    rows = cur.fetchall()
    con.close()

    # 2) ThreadPool으로 병렬 필터링
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_process_batch, batch)
            for batch in _chunked(rows, BATCH_SIZE)
        ]
        for fut in as_completed(futures):
            try:
                results.extend(fut.result())
            except Exception as e:
                print("Batch 처리 중 오류:", e)

    # 3) 결과를 새로운 테이블에 저장
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS password_train_only_korean;
        CREATE TABLE password_train_only_korean (
            email TEXT,
            password TEXT
        );
    """)
    cur.executemany(
        "INSERT INTO password_train_only_korean(email, password) VALUES (?, ?)",
        results
    )
    con.commit()
    con.close()

    print(f"완료: 총 {len(results):,}개 비밀번호 보존됨")

if __name__ == "__main__":
    main()
