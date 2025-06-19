from typing import List, Tuple, Optional

Seg = Tuple[str, Optional[str]]

def split_alpha(text: str) -> List[str]:
    segs, i, n = [], 0, len(text)
    while i < n:
        j = i + 1
        alpha = text[i].isalpha()
        while j < n and text[j].isalpha() == alpha:
            j += 1
        segs.append(text[i:j])
        i = j
    return segs

def detect_alphabet(section_list) -> List[str]:
    found, idx = [], 0
    while idx < len(section_list):
        txt, lbl = section_list[idx]
        if lbl is None:
            new = []
            for seg in split_alpha(txt):
                if seg.isalpha():
                    new.append((seg, f"A{len(seg)}"))
                    found.append(seg.lower())
                else:
                    new.append((seg, None))
            section_list[idx:idx + 1] = new
            idx += len(new)
        else:
            idx += 1
    return found