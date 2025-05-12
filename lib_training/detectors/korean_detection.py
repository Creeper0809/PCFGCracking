from typing import List, Tuple, Optional

# ── 두벌식 키보드 매핑 ──
_initial_map = {
    'r':0, 's':2, 'e':3, 'f':5, 'a':6, 'q':7, 't':9, 'd':11,
    'w':12, 'c':14, 'z':15, 'x':16, 'v':17, 'g':18
}
_medial_map = {
    'k':0, 'o':1, 'i':2, 'j':4, 'p':5, 'u':6,
    'h':8, 'y':12, 'n':13, 'b':17, 'm':18, 'l':20
}
# 2글자 조합 모아치기 (ㅘ, ㅙ, ㅚ, ㅝ, ㅞ, ㅟ, ㅢ)
_vowel_combine = {
    ('h','k'):9, ('h','o'):10, ('h','l'):11,
    ('n','j'):14, ('n','p'):15, ('n','l'):16,
    ('m','l'):19
}
# 종성에 올 수 있는 자음 (단일자음만)
_final_map = {
    'r':1, 's':4, 'e':7, 'f':8, 'a':16, 'q':17,
    't':19, 'd':21, 'w':22, 'c':23, 'z':24,
    'x':25, 'v':26, 'g':27
}

def _can_parse_hangul(s: str) -> bool:
    i, n = 0, len(s)
    while i < n:
        if s[i] not in _initial_map:
            return False
        i += 1
        if i < n:
            if i+1 < n and (s[i], s[i+1]) in _vowel_combine:
                i += 2
            elif s[i] in _medial_map:
                i += 1
            else:
                return False
        else:
            return False

        if i < n and s[i] in _final_map:
            nxt = s[i]
            if i+1 < n and (
                s[i+1] in _medial_map or
                (i+2 < n and (s[i+1], s[i+2]) in _vowel_combine)
            ):
                pass
            else:
                i += 1

    return True

def _split_hangul_prefixes(text: str) -> List[Tuple[str, Optional[str]]]:
    res: List[Tuple[str, Optional[str]]] = []
    lower_text = text.lower()
    i, n = 0, len(text)

    while i < n:
        found = False
        for j in range(n, i, -1):
            if _can_parse_hangul(lower_text[i:j]):
                res.append((text[i:j], f"H{j-i}"))
                i = j
                found = True
                break
        if found:
            continue
        k = i + 1
        while k < n:
            if any(_can_parse_hangul(lower_text[k:m]) for m in range(n, k, -1)):
                break
            k += 1
        res.append((text[i:k], None))
        i = k

    return res

def mark_hn_sections(sections):
    out = []
    temp_sections = []
    for txt, lbl in sections:
        if lbl is None:
            for txt2,lbl2 in _split_hangul_prefixes(txt):
                temp_sections.append((txt2, lbl2))
                if lbl2 is not None and lbl2.startswith("H"):
                    out.append(txt2.lower())
        else:
            temp_sections.append((txt, lbl))
    return out, temp_sections
