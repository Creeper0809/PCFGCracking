import functools
import math

from korean_dict.save_load import load_word_probs

probs = load_word_probs("//korean_dict/korean_dict/unigram_probs.json")

@functools.lru_cache(maxsize=10000)
def segment_word(
    text: str,
    max_len: int = 20,
    unk_base: float = 1e-3,
    split_penalty_known: float = 1.0,
    split_penalty_unk: float = 0.0  # 이걸로 조절
):
    n = len(text)
    log_unk = math.log(unk_base)

    dp = [(-math.inf, []) for _ in range(n + 1)]
    dp[0] = (0.0, [])

    for i in range(1, n + 1):
        best_score, best_seq = -math.inf, []
        for j in range(max(0, i - max_len), i):
            seg = text[j:i]

            is_known = seg in probs
            lp_seg = math.log(probs[seg]) if is_known else log_unk * len(seg)
            penalty = split_penalty_known if is_known else split_penalty_unk

            prev_score, prev_seq = dp[j]
            total_score = prev_score + lp_seg - penalty

            if total_score > best_score:
                best_score = total_score
                best_seq = prev_seq + [seg]

        dp[i] = (best_score, best_seq)

    return [
        (seg, f"H{len(seg)}") if seg in probs else (seg, None)
        for seg in dp[n][1]
    ]

def mark_hn_sections(sections):
    out = []
    temp_sections = []
    for txt, lbl in sections:
        if lbl is None:
            for txt2,lbl2 in segment_word(txt):
                temp_sections.append((txt2, lbl2))
                if lbl2 is not None and lbl2.startswith("H"):
                    out.append(txt2.lower())
        else:
            temp_sections.append((txt, lbl))
    return out, temp_sections

if __name__ == "__main__":
    print("minjaeminajae : ",segment_word("minjaeminjae"))
    print("p@$$w0rd2024!sual : ",segment_word("p@$$w0rd2024!sual0ve"))
    print("anfrlaclalswo : ",segment_word("anfrlaclalswo"))