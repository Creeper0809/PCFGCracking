import math
import functools
from typing import List, Tuple, Optional

from lib.training.detectors.alphabet_detection import split_alpha
from lib.training.util.english import is_english, is_valid_alpha_token, get_english_prob
from lib.training.util.korean import is_korean, get_Htoken_prob, is_pure_korean

Seg = Tuple[str, Optional[str]]  # 세그먼트 타입: (텍스트, 레이블)

#--------------------------------------------------------------------------------
# Segment Log Probability Section
#--------------------------------------------------------------------------------
def _segment_logprob(seg: str, log_unk: float) -> float:
    """
    세그먼트가 영어/한글인지 판별하여 로그 확률 반환.
    미분류(seg neither)인 경우 log_unk * 길이로 처리.
    """
    if is_english(seg):
        return get_english_prob(seg)  # 영어 단어 확률
    if is_korean(seg):
        return math.log(get_Htoken_prob(seg))  # 한글 토큰 로그 확률
    return log_unk * len(seg)  # 미분류 토큰

#--------------------------------------------------------------------------------
# Penalty Section
#--------------------------------------------------------------------------------
def _penalty(seg: str) -> float:
    """
    세그먼트 유형별 페널티 계산.
    영어/한글이면 텍스트 여부에 따라 경미한 페널티, 그 외엔 길이 기반 페널티.
    """
    if is_korean(seg) or is_english(seg):
        return 0.5 if seg.isalpha() else 1.0
    return len(seg) + (10 if len(seg) <= 2 and not seg.isalpha() else 5)

#--------------------------------------------------------------------------------
# Best Path DP Section
#--------------------------------------------------------------------------------
def _best_path(text: str, max_len: int, log_unk: float) -> List[str]:
    """
    DP를 이용해 텍스트를 최적 분할하여 분할 리스트 반환.
    """
    n = len(text)
    dp: List[Tuple[float, List[str]]] = [(-math.inf, []) for _ in range(n + 1)]
    dp[0] = (0.0, [])

    for i in range(1, n + 1):
        for j in range(max(0, i - max_len), i):
            seg = text[j:i]
            score = dp[j][0] + _segment_logprob(seg, log_unk) - _penalty(seg)
            if score > dp[i][0]:
                dp[i] = (score, dp[j][1] + [seg])
    return dp[n][1]

#--------------------------------------------------------------------------------
# Tag Segments Section
#--------------------------------------------------------------------------------
def _tag_segments(segments: List[str]) -> List[Seg]:
    """
    각 세그먼트에 H{길이} 또는 A{길이} 레이블, 그 외 None 부여.
    """
    tagged: List[Seg] = []
    for seg in segments:
        if is_korean(seg):
            tagged.append((seg, f"H{len(seg)}"))
        elif is_english(seg):
            tagged.append((seg, f"A{len(seg)}"))
        else:
            tagged.append((seg, None))
    return tagged

#--------------------------------------------------------------------------------
# Trim Bad Neighbors Section
#--------------------------------------------------------------------------------
def _trim_bad_neighbors(tagged: List[Seg]) -> List[Seg]:
    """
    주변에 라벨 없는 알파벳 단편(garbage alphabet)이 있으면 해당 H/A 라벨 제거.
    영단어 사이에 한글이 있다고 오판가능성이 크기 때문
    """
    clean: List[Seg] = []
    for i, (s, lab) in enumerate(tagged):
        if not (lab and lab[0] in "HA"):
            clean.append((s, lab))
            continue
        prev_bad = i > 0 and tagged[i-1][1] is None and is_valid_alpha_token(tagged[i-1][0])
        next_bad = i+1 < len(tagged) and tagged[i+1][1] is None and is_valid_alpha_token(tagged[i+1][0])
        clean.append((s, None if prev_bad or next_bad else lab))
    return clean

#--------------------------------------------------------------------------------
# Merge Unlabeled Section
#--------------------------------------------------------------------------------
def _merge_unlabeled(final: List[Seg]) -> List[Seg]:
    """
    연속된 라벨 None 세그먼트를 병합하여 단일 세그먼트로 합침.
    """
    merged: List[Seg] = []
    for s, lab in final:
        if lab is None and merged and merged[-1][1] is None:
            merged[-1] = (merged[-1][0] + s, None)
        else:
            merged.append((s, lab))
    return merged

#--------------------------------------------------------------------------------
# Check Unlabeled Alpha Section
#--------------------------------------------------------------------------------
def _has_unlabeled_alpha(segs: List[Seg]) -> bool:
    """
    None 라벨 세그먼트에 알파벳 문자가 포함되어 있는지 확인.
    """
    return any(lab is None and any(c.isalpha() for c in token) for token, lab in segs)

#--------------------------------------------------------------------------------
# Segment Word Section
#--------------------------------------------------------------------------------
def _try_transfrom_dubeol(text):
    splited_text = split_alpha(text)
    update = []
    for seg in splited_text:
        if not seg.isalpha():
            update.append((seg, None))
            continue
        if not is_pure_korean(seg):
            return False, None
        update.append((seg, f"H{len(seg)}"))
    return True, update

@functools.lru_cache(maxsize=10_000)
def _segment_word(text: str, max_len: int = 20) -> List[Seg]:
    """
    최적 분할, 태깅, 보정, 병합 순으로 처리하여 최종 세그먼트 리스트 반환.
    """
    is_pure, update = _try_transfrom_dubeol(text)
    if is_pure:
        return update
    log_unk = math.log(1e-3)
    best_segments = _best_path(text, max_len, log_unk)
    tagged = _tag_segments(best_segments)
    cleaned = _trim_bad_neighbors(tagged)
    merged = _merge_unlabeled(cleaned)
    return merged if not _has_unlabeled_alpha(merged) else [(text, None)]

#--------------------------------------------------------------------------------
# Public section
#--------------------------------------------------------------------------------
def detect_dictionary_word(sections: List[Seg]) -> List[Seg]:
    """
    None 라벨 구간을 재분할하여 레이블 부착된 세그먼트를 반환.
    """
    updated: List[Seg] = []
    for txt, lab in sections:
        if lab is not None:
            updated.append((txt, lab))
            continue
        for s_txt, s_lbl in _segment_word(txt):
            updated.append((s_txt, s_lbl))
    return updated