import itertools
from typing import List, Tuple, Optional, Set
from wordfreq import top_n_list

VALID_WORDS: Set[str] = set(top_n_list("en", n=100_000))

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

def normalize_leet(text: str) -> str:
    return ''.join(LEET_MAP.get(ch, ch) for ch in text)

def split_letter_nonletter(text: str) -> List[str]:
    segs, i = [], 0
    while i < len(text):
        is_alpha = text[i].isalpha()
        j = i
        while j < len(text) and text[j].isalpha() == is_alpha:
            j += 1
        segs.append(text[i:j])
        i = j
    return segs

def merge_letter_chunks(chunks: List[str]) -> List[Tuple[str, Optional[str]]]:
    out = []
    for chunk in chunks:
        if chunk.isalpha():
            if out and out[-1][1] is not None:
                prev, _ = out.pop()
                chunk = prev + chunk
            out.append((chunk, f"A{len(chunk)}"))
        else:
            out.append((chunk, None))
    return out

def is_valid(segmentation: List[Tuple[str, Optional[str]]]) -> bool:
    for s, lab in segmentation:
        if lab and lab.startswith("A"):
            if len(s) == 1:
                return False
            if s.lower() not in VALID_WORDS:
                return False
    return True

def recover_original_segmentation(original_text: str, segmentation: List[Tuple[str, Optional[str]]]) -> List[Tuple[str, Optional[str]]]:
    result = []
    i = 0
    for seg, label in segmentation:
        seg_len = len(seg)
        original_chunk = original_text[i:i + seg_len]
        result.append((original_chunk, label))
        i += seg_len
    return result

def meaningful_segmentations(text: str):
    chunks = split_letter_nonletter(text)
    non_alpha_idxs = [i for i, ch in enumerate(chunks) if not ch[0].isalpha()]
    results = []

    for r in range(1, len(non_alpha_idxs) + 1):
        for subset in itertools.combinations(non_alpha_idxs, r):
            mapped = [
                normalize_leet(chunks[i]) if i in subset else chunks[i]
                for i in range(len(chunks))
            ]
            segs = merge_letter_chunks(mapped)
            if is_valid(segs):
                results.append(segs)

    # 중복 제거
    unique = []
    seen = set()
    for seg in results:
        key = tuple(seg)
        if key not in seen:
            seen.add(key)
            unique.append(seg)

    all_segmentations = []
    for seg in unique:
        merged_text = ''.join(s for s, _ in seg)
        orig_segment = recover_original_segmentation(text, seg)
        all_segmentations.append(orig_segment)

    return all_segmentations


def detect_alphabet_mask(segmentation: List[Tuple[str, Optional[str]]]) -> List[Tuple[str, str]]:
    masks = []
    for s, lab in segmentation:
        if lab and lab.startswith("A"):
            masks.append(''.join('U' if c.isupper() else 'L' for c in s))
    return masks

def expand_all_segmentations(sections: List[Tuple[str, Optional[str]]]) -> List[List[Tuple[str, Optional[str]]]]:
    segment_options: List[List[List[Tuple[str, Optional[str]]]]] = []

    for text, label in sections:
        if label is None:
            segs = meaningful_segmentations(text)
            fallback = [(text, None)]
            if fallback not in segs:
                segs = [fallback] + segs
            else:
                segs = segs
            segment_options.append(segs)
        else:
            segment_options.append([[(text, label)]])
    all_combinations = list(itertools.product(*segment_options))
    seen = set()
    unique_sections = []

    for section in [sum(comb, []) for comb in all_combinations]:
        detect_alphabet(section)
        key = tuple(section)

        if key not in seen:
            seen.add(key)
            unique_sections.append(section)

    return unique_sections


def print_all_segmentations(sections: List[Tuple[str, Optional[str]]]):
    all_segs = expand_all_segmentations(sections)
    print(f"\n{len(all_segs)}개 전체 조합:")
    for i, segs in enumerate(all_segs, 1):
        print(f"[조합 {i}]")
        print(" ", segs)
        print("  마스크:", detect_alphabet_mask(segs))

if __name__ == "__main__":
    print("p@$$w0rd2024!sual0ve : ")
    sections = [('p@$$w0rd2024!', None), ('sua', 'H3'), ('l0ve', None)]
    print_all_segmentations(sections)
