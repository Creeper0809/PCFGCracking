from collections import Counter
from pathlib import Path
from typing import Dict
import json

from korean_dict.han2en import hangul_to_romanization, hangul_to_dubeolsik

def caculate_prob_and_save():
    final_items = load_checkpoint_counts(Path("korean_dict/korean_dict_filtered.json"))
    dubeol_ctr = Counter()
    for w, cnt in final_items.items():
        k = hangul_to_dubeolsik(w)
        try:
            for i in hangul_to_romanization(w):
                if i and len(i)> 2: dubeol_ctr[i] += cnt
        except Exception as e:
            print(f"[Warning] romanization failed for '{w}': {e}")
        if k and len(k)> 2: dubeol_ctr[k] += cnt

    V = len(dubeol_ctr)
    T = sum(dubeol_ctr.values())

    word_probs = {
        token: (count + 1) / (T + V)
        for token, count in dubeol_ctr.items()
    }
    prob_path = Path("korean_dict/unigram_probs.json")

    prob_path.parent.mkdir(parents=True, exist_ok=True)
    with prob_path.open("w", encoding="utf-8") as f:
        json.dump(word_probs, f, ensure_ascii=False, indent=2)

def load_word_probs(path: str) -> Dict[str, float]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_checkpoint_counts(path: Path) -> Counter:
    if not path.exists():
        return Counter()
    items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        return Counter(items)
    return Counter({w: cnt for w, cnt in items})


def load_checkpoint_done(path: Path) -> set:
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))

def save_checkpoint_counts(counter: Counter, path: Path):
    items = counter.most_common()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def save_checkpoint_done(done: set, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(done), ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    caculate_prob_and_save()
