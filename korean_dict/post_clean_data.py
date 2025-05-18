import re
from collections import Counter

from korean_dict.save_load import load_checkpoint_counts, save_checkpoint_counts
from pathlib import Path

_SUFFIX_RE = re.compile(r"^.+(?:합니다|습니다|는다고|으며|니까|하게|졌다|고요|하다|려고|지만"
                        r"|다는|니다|하고|해서|에도|는데|어요|어도|한데|리는|므로|히고|으로써|웠다|으면|찮)$")

RE_ONLY_HANGUL = re.compile(r'^[가-힣]{1,}$')
MEANINGFUL_SINGLE_CHAR = {
    "강", "불", "물", "눈", "빛", "힘", "맛", "별", "짱", "짤",
    "덕", "감", "일", "집", "방", "산", "띵", "팟", "흑", "헉",
    "금", "앗", "읍", "줄", "성", "장", "톡", "꿀", "움", "달"
}
CUSTOM_DICT = {
    "잼민" : 100000
}
def clean():
    path = Path("korean_dict/korean_dict.json")

    ctr = load_checkpoint_counts(path)
    filtered = Counter({
        w: cnt
        for w, cnt in ctr.items()
        if not _SUFFIX_RE.match(w)
           and RE_ONLY_HANGUL.fullmatch(w)
           and (len(w) > 1 or (len(w) == 1 and w in MEANINGFUL_SINGLE_CHAR))
    })
    filtered.update(CUSTOM_DICT)
    print(f"filtered {len(filtered)} words")
    new_path = Path("korean_dict/korean_dict_filtered.json")
    save_checkpoint_counts(filtered, new_path)

def print_filtered():
    path = Path("korean_dict/korean_dict.json")
    ctr = load_checkpoint_counts(path)
    for w, cnt in ctr.most_common():
        if len(w) == 1 and RE_ONLY_HANGUL.fullmatch(w):
            print(w)

if __name__ == "__main__":
    clean()