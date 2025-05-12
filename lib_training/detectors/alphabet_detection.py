from typing import List, Tuple, Optional

def split_alpha_special(text: str) -> List[str]:
    segs = []
    i, n = 0, len(text)
    while i < n:
        if text[i].isalpha():
            j = i + 1
            while j < n and text[j].isalpha():
                j += 1
        else:
            j = i + 1
            while j < n and not text[j].isalpha():
                j += 1
        segs.append(text[i:j])
        i = j
    return segs

def detect_alphabet(section_list) -> List[str]:
    found_alphas: List[str] = []
    idx = 0
    while idx < len(section_list):
        txt, lbl = section_list[idx]
        if lbl is None:
            parsing: List[Tuple[str, Optional[str]]] = []
            for seg in split_alpha_special(txt):
                if seg.isalpha():
                    parsing.append((seg, f"A{len(seg)}"))
                    found_alphas.append(seg.lower())
                else:
                    parsing.append((seg, None))
            section_list[idx:idx+1] = parsing
            idx += len(parsing)
        else:
            idx += 1
    return found_alphas


def detect_alphabet_mask(section_list):
    masks: List[Tuple[str, str]] = []
    for string, label in section_list:
        if not (label and (label.startswith('H') or label.startswith('A'))):
            continue
        mask = ''.join('U' if ch.isupper() else 'L' for ch in string)
        masks.append((string, mask))
    return masks


