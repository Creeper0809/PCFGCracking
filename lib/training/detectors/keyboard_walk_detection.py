from typing import List, Tuple, Optional

def _get_keyboard():
    return {
        'name': 'qwerty',
        'row1': list("1234567890-="),
        'row2': list("qwertyuiop[]\\"),
        'row3': list("asdfghjkl;'"),
        'row4': list("zxcvbnm,./")
    }

def find_keyboard_row_column(ch: str, keyboards: List[dict]) -> dict:
    pos = {}
    for kb in keyboards:
        for row_key in ('row1','row2','row3','row4'):
            if ch in kb[row_key]:
                pos[kb['name']] = (int(row_key[-1]), kb[row_key].index(ch))
    return pos

def is_adjacent_extended(a: Tuple[int,int], b: Tuple[int,int]) -> bool:
    return abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1

def detect_keyboard_walk(password: str, min_run: int = 4
) -> Tuple[List[Tuple[str, Optional[str]]], List[str], List[str]]:
    keyboards = [_get_keyboard()]
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

        if start_map:
            run_layouts = set(start_map.keys())
            prev_pos = {L: start_map[L] for L in run_layouts}
            j = i + 1
            while j < n and run_layouts:
                nxt = password[j]
                nxt_map = find_keyboard_row_column(nxt, keyboards)
                new_runs = {
                    L for L in run_layouts
                    if L in nxt_map and is_adjacent_extended(prev_pos[L], nxt_map[L])
                }
                if not new_runs:
                    break
                run_layouts = new_runs
                prev_pos = {L: nxt_map[L] for L in run_layouts}
                j += 1
            run_len = j - i

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
            buffer += password[i]
            i += 1

    if buffer:
        sections.append((buffer, None))

    seen = set()
    layouts = []
    for l in layouts_used:
        if l not in seen:
            seen.add(l)
            layouts.append(l)

    return sections, found, layouts
