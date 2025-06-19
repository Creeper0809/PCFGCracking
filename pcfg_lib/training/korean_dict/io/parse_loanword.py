import os, sqlite3, itertools, requests, time
from pcfg_lib import paths

SERVICE_KEY = ''
DB_PATH = os.path.join(paths.KOREAN_DICT_DB_PATH, "korean_dict.db")

BASE_URL = "https://korean.go.kr/kornorms/exampleReqList.do"
PARAMS = {
    "serviceKey": SERVICE_KEY,
    "langType": "0003",
    "resultType": "json",
    "numOfRows": 500,
}
BATCH_SIZE = 5000

DDL = """
CREATE TABLE IF NOT EXISTS LoanwordDict (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    word         TEXT,
    roman        TEXT,
    original     TEXT,
    foreign_type TEXT,
    country      TEXT,
    lang_type    TEXT,
    source       TEXT
);
"""


def fetch_items():
    for page in itertools.count(1):
        print("continuous fetch(page) : ", page, "")
        resp = requests.get(BASE_URL, params={**PARAMS, "pageNo": page}, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        response = payload["response"]
        if "items" not in response:
            continue
        for item in response["items"]:
            yield item
        if page * response["numofrows"] >= response["totalcount"]:
            break
        time.sleep(0.1)


def to_tuple(i):
    return (
        (i.get("korean_mark") or "").strip(),
        (i.get("srclang_mark") or "").strip(),
        (i.get("foreign_gubun") or "").strip(),
        (i.get("guk_nm") or "").strip(),
        (i.get("lang_nm") or "").strip(),
        (i.get("source") or "").strip(),
    )


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS LoanwordDict")
    cur.execute(DDL)

    buffer, total = [], 0
    for item in fetch_items():
        if not item.get("korean_mark"):
            continue
        buffer.append(to_tuple(item))

        if len(buffer) >= BATCH_SIZE:
            cur.executemany(
                "INSERT OR IGNORE INTO LoanwordDict "
                "(word, original, foreign_type, country, lang_type, source) "
                "VALUES (?,?,?,?,?,?,?)",
                buffer
            )
            conn.commit()
            total += len(buffer)
            print(f"  · {total:,}개 저장 완료")
            buffer.clear()

    if buffer:
        cur.executemany(
            "INSERT OR IGNORE INTO LoanwordDict "
            "(word, original, foreign_type, country, lang_type, source) "
            "VALUES (?,?,?,?,?,?,?)",
            buffer
        )
        conn.commit()
        total += len(buffer)

    conn.close()
    print(f"→ 총 {total:,}개 항목 저장 완료")


if __name__ == "__main__":
    main()
