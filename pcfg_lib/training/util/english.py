from typing import List, Tuple, Optional
from wordfreq import top_n_list, zipf_frequency

#=======================================================================================================
# Constants Section
#=======================================================================================================
Seg = Tuple[str, Optional[str]]  # 세그먼트 타입: (텍스트, 레이블)

# 베이스 영어 단어 사전 (상위 100k)
VALID_WORDS = set(top_n_list("en", n=100_000))
# 상위 20k 단어 (어떻게 필터링할지 결정)
_EN_TOP = set(top_n_list("en", n=20_000, wordlist="small"))
# 영어 모음 집합
_EN_VOWELS = set("aeiou")

LEET_MAP = {
    # A
    '4': 'a', '@': 'a', '/-\\': 'a', '^': 'a', '∂': 'a',
    # B
    '8': 'b', '|3': 'b', 'ß': 'b', '13': 'b', 'j3': 'b',
    # C
    '<': 'c', '(': 'c', '[': 'c', '{': 'c', '¢': 'c',
    # D
    '|)': 'd', '|>': 'd', '[)': 'd', 'cl': 'd',
    # E
    '3': 'e', '€': 'e', 'ë': 'e',
    # F
    '|=': 'f', 'ph': 'f',
    # G
    '6': 'g', 'gee': 'g', '&': 'g', '(_+': 'g',
    # H
    '#': 'h', '|-|': 'h', ']-[': 'h', '(-)': 'h', '}{': 'h',
    # I
    '1': 'i', '!': 'i', '|': 'i', 'eye': 'i',
    # J
    '_|': 'j', '_/': 'j', '_]': 'j', '_)': 'j',
    # K
    '|<': 'k', '|{': 'k', '1<': 'k', '7<': 'k',
    # L
    '1': 'l', '|_': 'l', '£': 'l',
    # M
    r'|\/|': 'm', r'\[\/\]': 'm', '(v)': 'm', '(V)': 'm', '^^': 'm',
    # N
    r'|\|': 'n', r'\[\\\]': 'n', '{\\}': 'n', r'\/': 'n',
    # O
    '0': 'o', '()': 'o', '[]': 'o', '<>': 'o', 'oh': 'o',
    # P
    '|*': 'p', '|o': 'p', '|>': 'p', '|°': 'p',
    # Q
    '0,': 'q', '(_,)' : 'q',
    # R
    '|2': 'r', '12': 'r', '|?': 'r', 'Я': 'r',
    # S
    '5': 's', '$': 's', '§': 's', 'z': 's',
    # T
    '7': 't', '+': 't', '-|-': 't', '†': 't',
    # U
    '(_)': 'u', '|_|': 'u', 'Ʉ': 'u',
    # V
    r'\\/': 'v', r'\\//': 'v', r'\/': 'v',
    # W
    r'\\/\\/': 'w', r'\\V/': 'w', r'\\|/': 'w', 'vv': 'w',
    # X
    '><': 'x', '}{': 'x', ')(': 'x', '×': 'x',
    # Y
    '`/': 'y', '¥': 'y',
    # Z
    '2': 'z', '%': 'z',
}

# 최소 길이 및 Zipf 빈도 임계값
MIN_LEN = 3
MIN_ZIPF = 4.0

#=======================================================================================================
# Token Validation Section
#=======================================================================================================
def is_valid_alpha_token(token: str) -> bool:
    # 길이 ≥3, 라틴 문자가 하나 이상 포함된 토큰인지 확인
    return len(token) > MIN_LEN and any(c.isalpha() for c in token)


def is_english(seg: str) -> bool:
    # 완전 알파벳, 상위 빈도 단어집에 존재, 모음 최소 2개, 길이 ≥3 확인
    lower = seg.lower()
    vcnt = sum(c in _EN_VOWELS for c in lower)
    return seg.isalpha() and lower in _EN_TOP and vcnt >= 2 and len(lower) >= MIN_LEN


def get_english_prob(seg: str) -> float:
    # 단어의 Zipf 빈도에 문자수 기반 가중치 추가
    return zipf_frequency(seg.lower(), "en") + len(seg) * 0.1

#=======================================================================================================
# Leet Mapping Section
#=======================================================================================================
def normalize_leet(text: str) -> str:
    # 문자열의 각 문자/패턴을 leet 매핑 규칙에 따라 디코딩
    return ''.join(LEET_MAP.get(c.lower(), c.lower()) for c in text)


def _good(word: str) -> bool:
    # 길이 및 Zipf 빈도 기준을 만족하는지 확인
    return len(word) >= MIN_LEN and zipf_frequency(word, "en") >= MIN_ZIPF


def _has_leet(raw: str) -> bool:
    # 원본에 leet 매핑이 실제 적용되었는지 확인
    return any(c.lower() in LEET_MAP and LEET_MAP[c.lower()] != c.lower() for c in raw)


def find_leet_words(text: str) -> List[Tuple[int,int,str,str]]:
    # 모든 부분 문자열에 대해 leet 디코딩 후 유효 단어 조건 검사
    n = len(text)
    hits: List[Tuple[int,int,str,str]] = []
    for i in range(n):
        for j in range(i + 2, n + 1):
            raw = text[i:j]
            decoded = normalize_leet(raw)
            if decoded.isalpha() and _good(decoded) and _has_leet(raw):
                hits.append((i, j, raw, decoded))
    return hits

#=======================================================================================================
# Mask Utilities Section
#=======================================================================================================
def get_alphabet_mask(segmentation: List[Seg]) -> List[str]:
    # 알파벳 레이블 세그먼트의 대/소문자 마스크 반환
    return [
        ''.join('U' if c.isupper() else 'L' for c in tok)
        for tok, lbl in segmentation if lbl and lbl.startswith('A')
]
