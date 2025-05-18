import re
from jamo import h2j, j2hcj
from korean_romanizer import Romanizer
from eunjeon import Mecab

import YaleKorean

DUBEOL_INITIAL = {
    'ㄱ': 'r', 'ㄲ': 'R', 'ㄴ': 's', 'ㄷ': 'e', 'ㄸ': 'E', 'ㄹ': 'f', 'ㅁ': 'a', 'ㅂ': 'q', 'ㅃ': 'Q',
    'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd', 'ㅈ': 'w', 'ㅉ': 'W', 'ㅊ': 'c', 'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g'
}
DUBEOL_MEDIAL = {
    'ㅏ': 'k', 'ㅐ': 'o', 'ㅑ': 'i', 'ㅒ': 'O', 'ㅓ': 'j', 'ㅔ': 'p', 'ㅕ': 'u', 'ㅖ': 'P',
    'ㅗ': 'h', 'ㅘ': 'hk', 'ㅙ': 'ho', 'ㅚ': 'hl', 'ㅛ': 'y',
    'ㅜ': 'n', 'ㅝ': 'nj', 'ㅞ': 'np', 'ㅟ': 'nl', 'ㅠ': 'b',
    'ㅡ': 'm', 'ㅢ': 'ml', 'ㅣ': 'l'
}
DUBEOL_FINAL = {
    '': '', 'ㄱ': 'r', 'ㄲ': 'R', 'ㄳ': 'rt', 'ㄴ': 's', 'ㄵ': 'sw', 'ㄶ': 'sg', 'ㄷ': 'e',
    'ㄹ': 'f', 'ㄺ': 'fr', 'ㄻ': 'fa', 'ㄼ': 'fq', 'ㄽ': 'ft', 'ㄾ': 'fx', 'ㄿ': 'fv', 'ㅀ': 'fg',
    'ㅁ': 'a', 'ㅂ': 'q', 'ㅄ': 'qt', 'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd', 'ㅈ': 'w', 'ㅊ': 'c',
    'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g'
}

PHONETIC_SPELLING_MAP = {
    # 모음 치환
    'ae': 'a',
    'ea': 'e',
    'ie': 'i',
    'oo': 'u',
    'ou': 'u',
    'ue': 'u',
    'ui': 'i',

    # 자음 치환
    'ph': 'f',
    'ck': 'k',
    'gh': 'g',
    'qu': 'k',
    'x': 'ks',
    'z': 's',

    # 발음화 치환
    'tion': 'shun',
    'sion': 'shun',
    'ture': 'cher',
    'dge': 'j',
    'ch': 'j',

    # 축약 표현
    'th': 'd',
    'wr': 'r'
}


def normalize_phonetic_spelling(romanized: str) -> str:
    for wrong, correct in PHONETIC_SPELLING_MAP.items():
        romanized = romanized.replace(wrong, correct)
    return romanized

def hangul_to_dubeolsik(text: str) -> str:
    result = []
    jamo_seq = j2hcj(h2j(text))
    for char in jamo_seq:
        if char in DUBEOL_INITIAL:
            result.append(DUBEOL_INITIAL[char])
        elif char in DUBEOL_MEDIAL:
            result.append(DUBEOL_MEDIAL[char])
        elif char in DUBEOL_FINAL:
            result.append(DUBEOL_FINAL[char])
        else:
            result.append(char)
    return ''.join(result)


def hangul_to_romanization(text: str):
    romanized = set()

    # 표준 로마자 표기
    romanized.add(YaleKorean.YaleCont(text))
    romanized.add(Romanizer(text).romanize())

    # 발음 기반 치환 적용
    normalized = {normalize_phonetic_spelling(r) for r in romanized}
    return romanized.union(normalized)


def load_stopwords(path: str) -> set[str]:
    from pathlib import Path
    stopfile = Path(path)
    stopwords = set()
    with stopfile.open(encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if not word or word.startswith('#'):
                continue
            stopwords.add(word)
    return stopwords

STOPWORDS = set(
    load_stopwords("///korean_dict//resource//STOPWORD.txt")
)

RE_HANGUL_TOKEN = re.compile(r"[가-힣]+")
mecab = Mecab()


def extract_clean_hangul(text: str):
    tokens = mecab.pos(text)
    NNG = []
    NNP = []
    for word, tag in tokens:
        if tag == "NNG":
            NNG.append(word)
        elif tag == "NNP":
            NNP.append(word)
    return list(set(NNG)), list(set(NNP))


if __name__ == "__main__":
    s = "잼민"
    print("두벌식  :", hangul_to_dubeolsik(s))
    print("발음식 영타:", hangul_to_romanization(s))

    print(mecab.pos("물 김치"))

