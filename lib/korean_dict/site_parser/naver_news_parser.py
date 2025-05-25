from lib.korean_dict.site_parser.site_parser import SiteParser

import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Iterator


class NaverNewsParser(SiteParser):
    HOST_RE = re.compile(r"(?:\w+\.)*news\.naver\.com$")
    PATH_RE = re.compile(r"/article/")

    def list_urls(self, html: str, base_url: str) -> Iterator[str]:
        soup = BeautifulSoup(html, "html.parser")
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(base_url, href)
            p = urlparse(full)
            if not self.HOST_RE.match(p.netloc):
                continue
            if not self.PATH_RE.search(p.path):
                continue
            if full in seen:
                continue
            seen.add(full)
            yield full

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # 1) PC 버전: articleBodyContents
        candidate = soup.select_one("#articleBodyContents")

        # 2) 모바일/신버전: <article id="dic_area">
        if not candidate:
            candidate = soup.select_one("article#dic_area")

        # 3) 모바일 다른 클래스명
        if not candidate:
            candidate = soup.select_one(".article_body")

        # 4) PC 신템플릿
        if not candidate:
            candidate = soup.select_one("div.newsc_article._article_body")

        if not candidate:
            # 찾지 못했으면 빈 문자열 리턴
            return ""

        # 불필요한 스크립트, 광고, 링크 등 제거
        for bad in candidate.select("script, .ad, .link_footer, .nclicks"):
            bad.decompose()

        # 텍스트만 추출
        return candidate.get_text(separator=" ", strip=True)
