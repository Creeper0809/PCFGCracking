import re

from lib.training.korean_dict.data_parser.BaseParser import BaseParser


class TabularNounParser(BaseParser):
    DIGIT_RE = re.compile(r'\d+')
    def parse(self, data_source):
        from collections import Counter
        try:
            text = data_source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = data_source.read_text(encoding="cp949")
        ctr = Counter()
        for line in text.splitlines():
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            _, word, pos = parts[:3]
            if pos.strip() != "명":
                continue
            clean = self.DIGIT_RE.sub("", word).strip()
            if clean:
                ctr[clean] += 1
        return ctr