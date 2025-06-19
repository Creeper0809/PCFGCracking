from itertools import product
from typing import List, Tuple, Optional

from pcfg_lib.training.util.english import find_leet_words

# 세그먼트 타입: (텍스트, 레이블)  레이블 예: 'A3' (디코딩된 길이)
Seg = Tuple[str, Optional[str]]


def _safe_sort_key(sequence: List[Seg]) -> Tuple[int, str]:
    """
    정렬 키 생성: 주로 세그먼트 개수, 부차적으로 텍스트를 이어 붙인 문자열
    """
    length = len(sequence)
    joined = ''.join(text for text, _ in sequence)
    return length, joined


def leet_segment(text: str) -> List[Seg]:
    """
    텍스트를 리트 단어와 나머지 조각으로 분할합니다.

    find_leet_words를 사용해 리트 단어 위치를 찾고, 겹치지 않는 매칭만 유지합니다.
    각 리트 세그먼트에 디코딩된 길이만큼 'A{n}' 레이블을 붙입니다.
    """
    # 시작 인덱스 기준, 매칭 길이 내림차순으로 후보 정렬
    candidates = sorted(
        find_leet_words(text),
        key=lambda match: (match[0], -(match[1] - match[0]))
    )

    chosen = []  # type: List[Tuple[int, int, str, str]]
    cursor = 0
    # 겹치지 않는 매칭만 선택
    for start, end, raw, decoded in candidates:
        if start >= cursor:
            chosen.append((start, end, raw, decoded))
            cursor = end

    segments: List[Seg] = []
    pos = 0
    for start, end, raw, decoded in chosen:
        # 리트 이전의 일반 텍스트 추가
        if pos < start:
            segments.append((text[pos:start], None))
        # 'A{디코딩된 길이}' 레이블을 붙인 리트 세그먼트 추가
        segments.append((raw, f"A{len(decoded)}"))
        pos = end

    # 남은 텍스트 추가
    if pos < len(text):
        segments.append((text[pos:], None))

    return segments


def all_merge_combinations(segments: List[Seg]) -> List[List[Seg]]:
    """
    인접 세그먼트를 병합하거나 그대로 두는 모든 조합을 생성합니다.

    n개의 세그먼트에 대해 2^(n-1)개의 병합 패턴을 고려합니다.
    병합 후, 결과 세그먼트가 원래 레이블이 붙은 리트 단어와 정확히 일치하면 레이블을 유지합니다.
    """
    if not segments:
        return []

    n = len(segments)
    results: List[List[Seg]] = []

    for mask in range(1 << (n - 1)):
        combo: List[Seg] = []
        current_text, current_label = segments[0]

        for i in range(1, n):
            next_text, next_label = segments[i]
            merge = not (mask & (1 << (i - 1)))
            if merge:
                # 현재와 다음 세그먼트 병합, 레이블 제거
                current_text += next_text
                current_label = None
            else:
                # 현재 세그먼트 확정
                combo.append((current_text, current_label))
                current_text, current_label = next_text, next_label

        combo.append((current_text, current_label))
        results.append(combo)

    # 일관된 순서를 위해 정렬
    results.sort(key=_safe_sort_key)
    return results


def comb_leets_sections(sections: List[Seg]) -> List[List[Seg]]:
    """
    레이블이 없는 구간에는 leet_segment와 병합 조합을 적용하여 변형을 생성하고,
    레이블이 있는 구간은 그대로 유지하여 모든 분할 조합을 만듭니다.
    """
    options: List[List[List[Seg]]] = []

    for text, label in sections:
        if label is None:
            base = leet_segment(text)
            variants = all_merge_combinations(base)
            # 원본 텍스트 세그먼트도 포함되도록 보장
            if [(text, None)] not in variants:
                variants.append([(text, None)])
            options.append(variants)
        else:
            # 레이블이 있는 세그먼트는 그대로 유지
            options.append([[(text, label)]])

    # 각 구간 변형의 데카르트 곱
    raw_combos = [sum(parts, []) for parts in product(*options)]

    # 중복 제거 및 순서 보존
    seen: set = set()
    unique: List[List[Seg]] = []
    for combo in raw_combos:
        key = tuple(combo)
        if key not in seen:
            seen.add(key)
            unique.append(combo)

    unique.sort(key=_safe_sort_key)
    return unique
