from typing import List, Tuple, Optional


def _get_keyboard():
    """QWERTY 키보드 레이아웃을 반환합니다."""
    return {
        'name': 'qwerty',
        'row1': list("1234567890-="),
        'row2': list("qwertyuiop[]\\"),
        'row3': list("asdfghjkl;'"),
        'row4': list("zxcvbnm,./")
    }


def find_keyboard_row_column(ch: str, keyboards: List[dict]) -> dict:
    """주어진 문자의 키보드상 위치(행, 열)를 찾습니다."""
    pos = {}
    for kb in keyboards:
        for row_key in ('row1', 'row2', 'row3', 'row4'):
            if ch in kb[row_key]:
                pos[kb['name']] = (int(row_key[-1]), kb[row_key].index(ch))
    return pos


def is_adjacent_extended(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """두 키가 서로 인접(대각선 포함)해 있는지 확인합니다."""
    return abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1


def detect_keyboard_walk(password: str, min_run: int = 4
                         ) -> Tuple[List[Tuple[str, Optional[str]]], List[str], List[str]]:
    """
    패스워드에서 반복 패턴 또는 키보드 이동 패턴을 탐지합니다.

    - 순수 반복 패턴 (예: 'aaaa')
    - 키보드 이동 패턴 (예: 'asdf'), 단, 중간에 멈춤(예: 'asdd')은 허용 안 함
    """
    keyboards = [_get_keyboard()]
    n = len(password)
    sections: List[Tuple[str, Optional[str]]] = []
    found: List[str] = []
    layouts_used: List[str] = []
    buffer = ""
    i = 0

    while i < n:
        run_len = 0
        final_run_layouts = set()

        # 1. 순수 반복 패턴 확인 (예: 'aaaa')
        j = i + 1
        while j < n and password[j].lower() == password[i].lower():
            j += 1

        if j - i >= min_run:
            run_len = j - i
            # 반복되는 문자가 포함된 모든 레이아웃이 유효합니다.
            start_map = find_keyboard_row_column(password[i].lower(), keyboards)
            if start_map:
                final_run_layouts = set(start_map.keys())

        # 2. 반복 패턴이 아닐 경우, 키보드 '이동' 패턴 확인 (예: 'asdf')
        else:
            start_map = find_keyboard_row_column(password[i].lower(), keyboards)
            walk_run_layouts = set()

            if start_map:
                walk_run_layouts = set(start_map.keys())
                prev_pos = {L: start_map[L] for L in walk_run_layouts}
                k = i + 1
                while k < n and walk_run_layouts:
                    # 이전 문자와 동일한 문자가 나오면 '이동'이 아니므로 패턴 중단
                    if password[k].lower() == password[k - 1].lower():
                        break

                    nxt = password[k].lower()
                    nxt_map = find_keyboard_row_column(nxt, keyboards)

                    new_runs = {
                        L for L in walk_run_layouts
                        if L in nxt_map and is_adjacent_extended(prev_pos[L], nxt_map[L])
                    }

                    if not new_runs:
                        break

                    walk_run_layouts = new_runs
                    prev_pos = {L: nxt_map[L] for L in walk_run_layouts}
                    k += 1

                walk_len = k - i
                if walk_len >= min_run:
                    run_len = walk_len
                    final_run_layouts = walk_run_layouts

        # 3. 발견된 패턴(반복 또는 이동)을 결과에 추가
        if run_len >= min_run:
            if buffer:
                sections.append((buffer, None))
                buffer = ""
            run_str = password[i:i + run_len]
            sections.append((run_str, 'K' + str(run_len)))
            found.append(run_str)
            if final_run_layouts:
                layouts_used.append(next(iter(final_run_layouts)))
            i += run_len
        else:
            buffer += password[i]
            i += 1

    if buffer:
        sections.append((buffer, None))

    # 사용된 레이아웃 목록 정리 (중복 제거)
    seen = set()
    layouts = []
    for l in layouts_used:
        if l not in seen:
            seen.add(l)
            layouts.append(l)

    return sections, found, layouts