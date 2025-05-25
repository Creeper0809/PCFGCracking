from collections import Counter

from lib.korean_dict.data_parser.BaseParser import BaseParser
from lib.korean_dict.util.han2en import extract_clean_hangul


class KoreanCopusParser(BaseParser):
    def parse(self, data) -> dict:
        ctr = Counter()
        for item in data["data_info"]:
            text = item.get("contents", "")
            NNG, NNP = extract_clean_hangul(text)
            for word in NNG:
                ctr[word] += 1
            for word in NNP:
                ctr[word] += 1

        return ctr

class YoutubeCommentParser(BaseParser):
    def parse(self, data) -> dict:
        ctr = Counter()
        for item in data["SJML"]["text"]:
            text = item.get("content", "")
            NNG, NNP = extract_clean_hangul(text)
            for word in NNG:
                ctr[word] += 1
            for word in NNP:
                ctr[word] += 1

        return ctr
