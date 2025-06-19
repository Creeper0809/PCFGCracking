import os
import re
import sqlite3
import itertools
from pathlib import Path

from jamo import h2j, j2hcj
from korean_romanizer import Romanizer
from eunjeon import Mecab
import YaleKorean

from pcfg_lib import paths

#=======================================================================================================
# Constants Section
#=======================================================================================================
# 두벌식 키보드 매핑
DUBEOL_INITIAL = {
    'ㄱ': 'r', 'ㄲ': 'R', 'ㄴ': 's', 'ㄷ': 'e', 'ㄸ': 'E', 'ㄹ': 'f',
    'ㅁ': 'a', 'ㅂ': 'q', 'ㅃ': 'Q', 'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd',
    'ㅈ': 'w', 'ㅉ': 'W', 'ㅊ': 'c', 'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g'
}
DUBEOL_MEDIAL = {
    'ㅏ': 'k', 'ㅐ': 'o', 'ㅑ': 'i', 'ㅒ': 'O', 'ㅓ': 'j', 'ㅔ': 'p',
    'ㅕ': 'u', 'ㅖ': 'P', 'ㅗ': 'h', 'ㅘ': 'hk', 'ㅙ': 'ho', 'ㅚ': 'hl',
    'ㅛ': 'y', 'ㅜ': 'n', 'ㅝ': 'nj', 'ㅞ': 'np', 'ㅟ': 'nl', 'ㅠ': 'b',
    'ㅡ': 'm', 'ㅢ': 'ml', 'ㅣ': 'l'
}
DUBEOL_FINAL = {
    'ㄱ': 'r', 'ㄲ': 'R', 'ㄳ': 'rt', 'ㄴ': 's', 'ㄵ': 'sw',
    'ㄶ': 'sg', 'ㄷ': 'e', 'ㄹ': 'f', 'ㄺ': 'fr', 'ㄻ': 'fa', 'ㄼ': 'fq',
    'ㄽ': 'ft', 'ㄾ': 'fx', 'ㄿ': 'fv', 'ㅀ': 'fg', 'ㅁ': 'a', 'ㅂ': 'q',
    'ㅄ': 'qt', 'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd', 'ㅈ': 'w', 'ㅊ': 'c',
    'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g'
}
# 두벌식 역매핑
REV_INITIAL = {v: k for k, v in DUBEOL_INITIAL.items()}
REV_MEDIAL  = {v: k for k, v in DUBEOL_MEDIAL.items()}
REV_FINAL   = {v: k for k, v in DUBEOL_FINAL.items()}

# 자모 유니코드 블록 및 인덱스
INITIAL = 0x001
MEDIAL = 0x010
FINAL = 0x100
CHAR_LISTS = {
    INITIAL: list(map(chr, [0x3131,0x3132,0x3134,0x3137,0x3138,0x3139,0x3141,0x3142,0x3143,0x3145,0x3146,0x3147,0x3148,0x3149,0x314A,0x314B,0x314C,0x314D,0x314E])),
    MEDIAL:  list(map(chr, [0x314F,0x3150,0x3151,0x3152,0x3153,0x3154,0x3155,0x3156,0x3157,0x3158,0x3159,0x315A,0x315B,0x315C,0x315D,0x315E,0x315F,0x3160,0x3161,0x3162,0x3163])),
    FINAL:   list(map(chr, [0x3131,0x3132,0x3133,0x3134,0x3135,0x3136,0x3137,0x3139,0x313A,0x313B,0x313C,0x313D,0x313E,0x313F,0x3140,0x3141,0x3142,0x3144,0x3145,0x3146,0x3147,0x3148,0x314A,0x314B,0x314C,0x314D,0x314E]))
}
CHAR_SETS = {k: set(v) for k, v in CHAR_LISTS.items()}
CHARSET = set(itertools.chain(*CHAR_SETS.values()))
CHAR_INDICES = {k: {c: i for i, c in enumerate(v)} for k, v in CHAR_LISTS.items()}

# 발음 규칙 기반 치환 맵
PHONETIC_SPELLING_MAP = {
    'ae': 'a','ea': 'e','ie': 'i','oo': 'u','ou': 'u','ue': 'u','ui': 'i',
    'ph': 'f','ck': 'k','gh': 'g','qu': 'k','x': 'ks','z': 's',
    'tion': 'shun','sion': 'shun','ture': 'cher','dge': 'j','ch': 'j',
    'th': 'd','wr': 'r'
}

# 확률 사전 DB 경로
_KO_DB = paths.KOREAN_DICT_DB_PATH

#=======================================================================================================
# Hangul Detection Section
#=======================================================================================================

def is_hangul_syllable(c):
    # 완성형 한글 음절(U+AC00~U+D7A3)인지 확인
    return 0xAC00 <= ord(c) <= 0xD7A3


def is_hangul_jamo(c):
    # 합성용 자모(U+1100~U+11FF)인지 확인
    return 0x1100 <= ord(c) <= 0x11FF


def is_hangul_compat_jamo(c):
    # 호환 자모(U+3130~U+318F)인지 확인
    return 0x3130 <= ord(c) <= 0x318F


def is_hangul_jamo_exta(c):
    # Jamo Extended-A 범위인지 확인
    return 0xA960 <= ord(c) <= 0xA97F


def is_hangul_jamo_extb(c):
    # Jamo Extended-B 범위인지 확인
    return 0xD7B0 <= ord(c) <= 0xD7FF


def is_supported_hangul(c):
    # 지원하는 한글 문자 범위(완성형 혹은 호환 자모)
    return is_hangul_syllable(c) or is_hangul_compat_jamo(c)


def is_contains_single_jamo(text: str) -> bool:
    # 문자열에 호환 자모 단일 문자가 하나라도 있는지 확인
    return any(is_hangul_compat_jamo(ch) for ch in text)


def check_hangul(c, jamo_only=False):
    # 지원하지 않는 문자일 경우 예외 발생
    if not ((jamo_only or is_hangul_compat_jamo(c)) or is_supported_hangul(c)):
        raise ValueError(
            f"'{c}'는 지원되지 않는 한글 문자입니다."
        )

#=======================================================================================================
# Romanization & Caps Section
#=======================================================================================================

def normalize_phonetic_spelling(romanized: str) -> str:
    # 발음 기반 치환 규칙을 적용하여 로마자 정규화
    for wrong, correct in PHONETIC_SPELLING_MAP.items():
        romanized = romanized.replace(wrong, correct)
    return romanized


def hangul2dubeol(text: str) -> str:
    # 한글 문자열을 두벌식 키 입력 시퀀스로 변환
    result = []
    # jamo 분리
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


def hangul2roman(text: str) -> set:
    # Yale 및 일반 로마자 변환 후, 발음 규칙 정규화 결과 병합
    romans = {YaleKorean.YaleCont(text), Romanizer(text).romanize()}
    normalized = {normalize_phonetic_spelling(r) for r in romans}
    return romans.union(normalized)


def roman2jamo(seq: str) -> list[str] | None:
    # 로마자 시퀀스를 두벌식 자모 리스트로 변환
    i = 0; jamos = []
    # 키 시퀀스 길이 내림차순 정렬
    all_keys = sorted(
        list(REV_INITIAL) + list(REV_MEDIAL) + list(REV_FINAL),
        key=len, reverse=True
    )
    while i < len(seq):
        flag = False
        for k in all_keys:
            if seq.startswith(k, i):
                # 역매핑 후 자모 추가
                jamos.append(REV_INITIAL.get(k) or REV_MEDIAL.get(k) or REV_FINAL.get(k))
                i += len(k)
                flag = True
                break
        if not flag:
            return None
    return jamos

def get_korean_caps_mask(segs: list[tuple[str, str]]) -> list[str]:
    # 한글 세그먼트의 대/소문자 마스크 생성
    return [
        ''.join('U' if c.isupper() else 'L' for c in txt)
        for txt, lab in segs if lab and lab.startswith('H')
    ]

#=======================================================================================================
# Stopwords Section
#=======================================================================================================

def load_stopwords(path: str) -> set[str]:
    # 불용어 파일에서 주석과 빈 줄을 제외하고 단어 로드
    stopfile = Path(path)
    stopwords = set()
    with stopfile.open(encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith('#'):
                stopwords.add(word)
    return stopwords

# 불용어셋 초기화
STOPWORDS = load_stopwords(os.path.join(paths.DATA_PATH, "STOPWORD.txt"))
# 한글 토큰 정규식 및 형태소 분석기
RE_HANGUL_TOKEN = re.compile(r"[가-힣]+")
mecab = Mecab()

#=======================================================================================================
# Noun Extraction Section
#=======================================================================================================

def extract_clean_hangul(text: str) -> tuple[list[str], list[str]]:
    # NN... tags 이용해 일반 명사(NNG)와 고유 명사(NNP) 추출
    tokens = mecab.pos(text)
    NNG, NNP = [], []
    for word, tag in tokens:
        if tag == "NNG": NNG.append(word)
        elif tag == "NNP": NNP.append(word)
    return list(set(NNG)), list(set(NNP))

#=======================================================================================================
# Probability Section
#=======================================================================================================

def _load_probs() -> dict[str, float]:
    # SQLite에서 unigram 확률 로드
    with sqlite3.connect(_KO_DB) as conn:
        return {token: prob for token, prob in conn.execute(
            "SELECT token, probability FROM UnigramProbs"
        )}

# 확률 사전 및 버킷 초기화
PROBS = _load_probs()
_BUCKET: dict[str, list[str]] = {}
for tok in PROBS:
    _BUCKET.setdefault(tok.casefold(), []).append(tok)


def _matches_case(key: str, txt: str) -> bool:
    # 대소문자 패턴이 일치하는지 확인
    return len(key) == len(txt) and all(
        (k == t if k.isupper() else k == t.lower())
        for k, t in zip(key, txt)
    )


def get_original(roman: str) -> str | None:
    # 로마자에 대응하는 원래 한글 토큰 반환
    for cand in _BUCKET.get(roman.casefold(), []):
        if _matches_case(cand, roman):
            return cand
    return None


def get_Htoken_prob(token: str) -> float:
    # 토큰의 unigram 확률 반환
    orig = get_original(token)
    return PROBS.get(orig, 0)

#=======================================================================================================
# Token Utilities Section
#=======================================================================================================

def is_korean(token: str) -> bool:
    # 사전 매칭 여부 확인
    orig = get_original(token)
    return bool(orig and len(orig) >= 2)

def is_pure_korean(token):
    # 로마자→자모→한글 변환 후 단일 자모 포함 여부 및 길이 검사
    jamo = roman2jamo(token)
    hang = join_jamos(''.join(jamo)) if jamo else None
    if hang and not is_contains_single_jamo(hang) and len(hang) > 2:
        return True
    return False


def get_jamo_type(c: str) -> int:
    # 자모 타입(초/중/종성) 반환
    check_hangul(c)
    # 호환 자모만 처리
    assert is_hangul_compat_jamo(c), f"not a jamo: {ord(c):x}"
    return sum(t for t, s in CHAR_SETS.items() if c in s)

#=======================================================================================================
# Jamo Composition Section
#=======================================================================================================

def join_jamos_char(init: str, med: str, final: str | None = None) -> str:
    # 초·중·종성 자모를 합쳐 한글 음절 생성
    for c in filter(None, (init, med, final)):
        check_hangul(c, jamo_only=True)
    i = CHAR_INDICES[INITIAL][init]
    m = CHAR_INDICES[MEDIAL][med]
    f = 0 if final is None else CHAR_INDICES[FINAL][final] + 1
    return chr(0xAC00 + 28 * 21 * i + 28 * m + f)


def join_jamos(s: str, ignore_err: bool = True) -> str:
    # 자모 시퀀스를 합쳐 완성형 한글 문자열 생성
    last_t = 0; queue: list[str] = []; result = ""

    def flush(n: int = 0) -> str | None:
        buf = []
        while len(queue) > n:
            buf.append(queue.pop())
        if len(buf) == 1:
            return buf[0] if ignore_err else (_ for _ in ()).throw(ValueError(f"invalid jamo: {buf[0]}"))
        if len(buf) >= 2:
            try:
                return join_jamos_char(*buf)
            except Exception:
                return ''.join(buf) if ignore_err else (_ for _ in ()).throw(ValueError(f"invalid jamos: {buf}"))
        return None

    for c in s:
        if c not in CHARSET:
            # 자모 외 문자는 바로 추가
            if queue:
                new_c = flush() + c
            else:
                new_c = c
            last_t = 0
        else:
            # 자모 통합 로직
            t = get_jamo_type(c); new_c = None
            if t & FINAL == FINAL:
                if last_t != MEDIAL: new_c = flush()
            elif t == INITIAL:
                new_c = flush()
            elif t == MEDIAL:
                if last_t & INITIAL == INITIAL:
                    new_c = flush(1)
                else:
                    new_c = flush()
            last_t = t; queue.insert(0, c)
        if new_c:
            result += new_c
    if queue:
        final_seg = flush()
        if final_seg: result += final_seg
    return result
