import re
from collections.abc import Iterator

import requests

from korean_dict.site_parser.site_parser import SiteParser
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from collections.abc import Iterator
from korean_dict.site_parser.site_parser import SiteParser
from urllib.parse import urlparse, parse_qs, urljoin
from bs4 import BeautifulSoup
import re
import aiohttp

class DcinsideParser(SiteParser):
    VIEW_BASE = "https://gall.dcinside.com/board/view/"
    POSTS_PER_BLOCK = 5000

    def list_urls(self, html: str, base_url: str) -> Iterator[str]:

        parsed = urlparse(base_url)
        board_id = parse_qs(parsed.query).get("id", [None])[0]
        if not board_id:
            return

        soup = BeautifulSoup(html, "html.parser")
        first_tr = soup.select_one("tr.ub-content.us-post")
        print(html)
        if not first_tr or not first_tr.has_attr("data-no"):
            return
        total_posts = int(first_tr["data-no"])

        block = self.POSTS_PER_BLOCK
        recent_nos = range(total_posts,     total_posts - block,    -1)
        mid_center  = total_posts // 2
        middle_nos  = range(mid_center + block//2, mid_center - block//2, -1)
        first_nos   = range(1, block + 1)

        # 4) 각 no마다 곧바로 view URL 생성
        for no in list(recent_nos) + list(middle_nos) + list(first_nos):
            print(f"{self.VIEW_BASE}?id={board_id}&no={no}&page=1")
            yield f"{self.VIEW_BASE}?id={board_id}&no={no}&page=1"

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.select_one(".writing_view_box")
        return body.get_text(" ", strip=True) if body else ""

