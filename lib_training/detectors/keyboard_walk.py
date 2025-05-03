#!/usr/bin/env python3
from typing import List, Tuple, Optional

def _get_us_keyboard():
    return {
        'name': 'qwerty',
        'row1': list("1234567890-="),
        'row2': list("qwertyuiop[]\\"),
        'row3': list("asdfghjkl;'"),
        'row4': list("zxcvbnm,./")
    }

def _get_jcuken_keyboard():
    return {
        'name': 'jcuken',
        'row1': list("1234567890-="),
        'row2': list("йцукенгшщзхъ\\"),
        'row3': list("фывапролджэ"),
        'row4': list("ячсмитьбю")
    }

def find_keyboard_row_column(ch: str, keyboards: List[dict]) -> dict:
    pos = {}
    for kb in keyboards:
        for row_key in ('row1','row2','row3','row4'):
            if ch in kb[row_key]:
                pos[kb['name']] = (int(row_key[-1]), kb[row_key].index(ch))
    return pos

def is_adjacent(a: Tuple[int,int], b: Tuple[int,int]) -> bool:
    pr, pc = a; cr, cc = b
    # 같은 행에서 좌우 인접 또는 반복
    if pr == cr and abs(pc - cc) <= 1:
        return True
    # 같은 열에서 상하 인접 또는 반복
    if pc == cc and abs(pr - cr) <= 1:
        return True
    return False

def detect_keyboard_walk(password: str, min_run: int = 3
) -> Tuple[List[Tuple[str, Optional[str]]], List[str], List[str]]:
    """
    키보드 행(가로) 및 열(세로) 워크를 탐지합니다.
    min_run 길이 이상의 연속된 인접 키만 K마스크로 분리하고,
    나머지는 버퍼에 모아 섹션으로 반환합니다.
    """
    keyboards = [_get_us_keyboard(), _get_jcuken_keyboard()]
    n = len(password)
    sections: List[Tuple[str, Optional[str]]] = []
    found: List[str] = []
    layouts_used: List[str] = []
    buffer = ""
    i = 0

    while i < n:
        start_map = find_keyboard_row_column(password[i], keyboards)
        run_len = 0
        run_layouts = set()

        # 매핑 가능한 키로 워크 시도
        if start_map:
            run_layouts = set(start_map.keys())
            prev_pos = {L: start_map[L] for L in run_layouts}
            j = i + 1
            while j < n and run_layouts:
                nxt = password[j]
                nxt_map = find_keyboard_row_column(nxt, keyboards)
                new_runs = {
                    L for L in run_layouts
                    if L in nxt_map and is_adjacent(prev_pos[L], nxt_map[L])
                }
                if not new_runs:
                    break
                run_layouts = new_runs
                prev_pos = {L: nxt_map[L] for L in run_layouts}
                j += 1
            run_len = j - i

        # 워크 길이 기준 만족 시, 버퍼 플러시 후 워크 섹션 추가
        if run_len >= min_run:
            if buffer:
                sections.append((buffer, None))
                buffer = ""
            run_str = password[i:i+run_len]
            sections.append((run_str, 'K' + str(run_len)))
            found.append(run_str)
            layouts_used.append(next(iter(run_layouts)))
            i += run_len
        else:
            # 워크 아닌 경우 버퍼에 추가
            buffer += password[i]
            i += 1

    # 남은 버퍼 플러시
    if buffer:
        sections.append((buffer, None))

    # 레이아웃 중복 제거
    seen = set()
    layouts = []
    for l in layouts_used:
        if l not in seen:
            seen.add(l)
            layouts.append(l)

    return sections, found, layouts
