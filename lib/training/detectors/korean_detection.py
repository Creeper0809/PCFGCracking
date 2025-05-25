import functools
import math
import os
import sqlite3

from lib import config

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_token = False

def load_word_probs_from_sqlite():
    db_path = os.path.join(config.KOREAN_PATH, "korean_dict.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT token, probability FROM UnigramProbs")
    rows = cur.fetchall()
    conn.close()
    return {token: prob for token, prob in rows}

probs = load_word_probs_from_sqlite()

buckmap = {}
for rom in probs.keys():
    key = rom.casefold()
    buckmap.setdefault(key, []).append(rom)

def _matches_phonemic_case(rom_key, text):
    if len(rom_key) != len(text):
        return False
    for r_char, t_char in zip(rom_key, text):
        if r_char.isupper():
            if t_char != r_char:
                return False
        else:
            if t_char.lower() != r_char:
                return False
    return True

def get_original(roman):
    lower_key = roman.casefold()
    for candidate in buckmap.get(lower_key, []):
        if _matches_phonemic_case(candidate, roman):
            return candidate
    return None

def get_korean_caps_mask(segmentations):
    masks = []
    for txt, label in segmentations:
        if label and label.startswith("H"):
            original = get_original(txt)
            mask = ""
            for o_char, t_char in zip(original, txt):
                mask += "L" if o_char == t_char else ("U" if t_char.isupper() else "L")
            masks.append(mask)
    return masks

@functools.lru_cache(maxsize=10000)
def segment_word(
    text: str,
    max_len: int = 20,
    unk_base: float = 1e-3,
    split_penalty_known: float = 1.0,
    split_penalty_unk: float = 0.0
):
    n = len(text)
    log_unk = math.log(unk_base)

    dp = [(-math.inf, []) for _ in range(n + 1)]
    dp[0] = (0.0, [])

    for i in range(1, n + 1):
        best_score, best_seq = -math.inf, []
        for j in range(max(0, i - max_len), i):
            seg = text[j:i]
            original = get_original(seg)
            is_known = original is not None
            lp_seg = math.log(probs[original]) if is_known else log_unk * len(seg)
            penalty = split_penalty_known if is_known else split_penalty_unk

            prev_score, prev_seq = dp[j]
            total_score = prev_score + lp_seg - penalty

            if total_score > best_score:
                best_score = total_score
                best_seq = prev_seq + [seg]

        dp[i] = (best_score, best_seq)

    return [
        (seg, f"H{len(seg)}") if get_original(seg) is not None else (seg, None)
        for seg in dp[n][1]
    ]

def mark_hn_sections(sections):
    out = []
    temp_sections = []
    for txt, lbl in sections:
        if lbl is None:
            for txt2, lbl2 in segment_word(txt):
                temp_sections.append((txt2, lbl2))
                if lbl2 and lbl2.startswith("H"):
                    out.append(txt2)
        else:
            temp_sections.append((txt, lbl))
    return out, temp_sections

if __name__ == "__main__":
    print("minjaeminajae :", segment_word("minjaeminjae"))
    print("p@$$w0rd2024!sual0ve :", segment_word("p@$$w0rd2024!sual0ve"))
    print("anfrlaclalswo :", segment_word("anfrlaclalswo"))
    print("get_original test:", get_original("RKaSid"))
