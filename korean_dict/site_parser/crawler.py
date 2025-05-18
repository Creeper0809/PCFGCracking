import asyncio
import re

from collections import Counter
from typing import List, Dict
import aiohttp

from han2en import hangul_to_dubeolsik, extract_clean_hangul
from korean_dict.han2en import hangul_to_romanization
from korean_dict.site_parser.parser_registry import get_parser_for

MAX_LIST_CONCURRENCY = 5
MAX_ART_CONCURRENCY = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://gall.dcinside.com/"
}

async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, headers=HEADERS, timeout=10) as resp:
        print("GET", url, "→", resp.status)
        print(await resp.read())
        raw = await resp.read()
        return raw.decode('euc-kr', errors='ignore')

async def crawl_list_pages(seeds: List[str], list_queue: asyncio.Queue):
    sem = asyncio.Semaphore(MAX_LIST_CONCURRENCY)
    async with aiohttp.ClientSession() as sess:
        async def worker(u):
            async with sem:
                html = await fetch(sess, u)
                print(html)
                parser = get_parser_for(u)
                if parser:
                    for art in parser.list_urls(html, u):
                        await list_queue.put(art)
        await asyncio.gather(*(worker(u) for u in seeds))
    for _ in range(MAX_ART_CONCURRENCY):
        await list_queue.put(None)

async def crawl_articles(list_queue: asyncio.Queue, counter: Counter):
    sem = asyncio.Semaphore(MAX_ART_CONCURRENCY)
    async with aiohttp.ClientSession() as sess:
        while True:
            url = await list_queue.get()
            if url is None:
                list_queue.task_done()
                break
            try:
                async with sem:
                    html = await fetch(sess, url)
                    parser = get_parser_for(url)
                    if parser:
                        text = parser.extract_text(html)
                        for frag in re.findall(r"[가-힣]+", text):
                            for w in extract_clean_hangul(frag):
                                print(w)
                                counter[w] += 1
            finally:
                list_queue.task_done()

def build_counter(hangul_counter: Counter) -> Counter:
    d = Counter()
    for w, cnt in hangul_counter.items():
        k = hangul_to_dubeolsik(w)
        if k:
            d[k] += cnt
        roman = hangul_to_romanization(w)
        if roman:
            d[roman] += cnt
    return d

def build_word_probs(dubeol_counter: Counter) -> Dict[str, float]:
    V = len(dubeol_counter)
    T = sum(dubeol_counter.values())
    return {w: (cnt+1)/(T+V) for w, cnt in dubeol_counter.items()}

async def main():
    seeds = [f"https://news.naver.com/section/{i}" for i in range(100, 105)]

    board_id = [
        "w_entertainer","m_entertainer_new1","ib_new2","comic_new4","neostock","cs_new1","tree","bitcoins_new1","leagueoflegends6"
    ]
    for bid in board_id:
        seeds.append(f"https://gall.dcinside.com/board/lists/?id={bid}&page=1")

    list_queue = asyncio.Queue(maxsize=1000)
    counter_hangul = Counter()
    task_list = asyncio.create_task(crawl_list_pages(seeds, list_queue))
    art_tasks = [asyncio.create_task(crawl_articles(list_queue, counter_hangul))
                 for _ in range(MAX_ART_CONCURRENCY)]
    await task_list
    await list_queue.join()
    for t in art_tasks:
        await t
    dubeol_counter = build_counter(counter_hangul)
    probs = build_word_probs(dubeol_counter)

    print(probs)

if __name__ == "__main__":
    asyncio.run(main())
