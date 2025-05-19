import re
from collections import Counter

from korean_dict.data_parser.BaseParser import BaseParser
from korean_dict.util.han2en import extract_clean_hangul


class NewWordParser(BaseParser):
    def parse(self, data) -> Counter:
        ctr = Counter()
        for item in data:
            term = item.get("term", "").strip()
            if term:
                NNG,NNP = extract_clean_hangul(term)
                for word in NNG:
                    ctr[word] += 1
                for word in NNP:
                    ctr[word] += 1
        return ctr

class NewWordParser2(BaseParser):
    def parse(self, data) -> Counter:
        ctr = Counter()
        for item in data:
            sentence = item.get("sentence", "")
            NNG, NNP = extract_clean_hangul(sentence)
            for word in NNG:
                ctr[word] += 1
            for word in NNP:
                ctr[word] += 1

            src_text = item.get("source", {}).get("text", "")
            NNG, NNP = extract_clean_hangul(src_text)
            for word in NNG:
                ctr[word] += 1
            for word in NNP:
                ctr[word] += 1

        return ctr

class NewWordParser3(BaseParser):
    RE_HANGUL_SEQ = re.compile(r"[가-힣]+")
    def parse(self, data) -> Counter:
        ctr = Counter()
        for key,value in data.items():
            for frag in self.RE_HANGUL_SEQ.findall(key):
                ctr[frag] += int(value["frequency"])
        return ctr

