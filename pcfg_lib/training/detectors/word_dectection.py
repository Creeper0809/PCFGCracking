import math
import os
import sys
import threading
import functools
from typing import List, Tuple, Optional

import fasttext
from pcfg_lib import paths
from pcfg_lib.training.detectors.alphabet_detection import split_alpha
from pcfg_lib.training.util.english import is_english, get_english_prob
from pcfg_lib.training.util.korean import is_korean, get_Htoken_prob, roman2jamo, join_jamos, is_pure_korean


Seg = Tuple[str, Optional[str]]

_model: Optional[fasttext.FastText] = None
_model_lock = threading.Lock()
_model_load_failed = False

def get_model() -> Optional[fasttext.FastText]:
    global _model, _model_load_failed
    if _model_load_failed:
        return None
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    model_path = os.path.join(paths.DATA_PATH, "model_quantized.ftz")
                    _model = fasttext.load_model(model_path)
                except Exception as e:
                    _model_load_failed = True
                    print(f"경고: FastText 모델 로드 실패: {e}")
                    return None
    return _model

def _get_dubeolshik_label(seg: str) -> Optional[str]:
    if not seg.isalpha():
        return None

    jamo_list = roman2jamo(seg)
    if jamo_list is None or not is_pure_korean(seg):
        return None

    if not is_korean(seg):
        return None

    hangul_word = join_jamos("".join(jamo_list))

    syllable_count = len(hangul_word)
    if syllable_count > 0:
        return f"K{syllable_count}"
    return None

def _segment_logprob(
        seg: str,
        log_unk: float,
        prob_thresh: float = 0.6,
        match_bonus: float = 0.5
    ) -> Tuple[float, Optional[str]]:

    dubeolshik_label = _get_dubeolshik_label(seg)
    if dubeolshik_label:
        return 1, dubeolshik_label

    if len(seg) == 1:
        return log_unk * len(seg), None

    if is_english(seg):
        dict_label = f"A{len(seg)}"
        dict_logp = get_english_prob(seg)
    elif is_korean(seg):
        dict_label = f"H{len(seg)}"
        dict_logp = math.log(get_Htoken_prob(seg))
    else:
        dict_label = None
        dict_logp = log_unk * len(seg)

    model = get_model()
    if model and seg.isalpha():
        labels, probs = model.predict(seg, k=1)
        if probs and probs[0] >= prob_thresh:
            raw = labels[0].replace("__label__", "")
            if raw == 'ko':
                prefix = 'H'
            elif raw == 'en':
                prefix = 'A'
            else:
                prefix = None
            if prefix:
                model_label = f"{prefix}{len(seg)}"
                model_logp = math.log(probs[0])
            else:
                model_label = None
                model_logp = log_unk * len(seg)
        else:
            model_label = None
            model_logp = log_unk * len(seg)
    else:
        model_label = None
        model_logp = log_unk * len(seg)

    if dict_label and model_label and dict_label == model_label:
        return dict_logp + model_logp + match_bonus, model_label
    if model_label:
        return model_logp, model_label
    if dict_label:
        return dict_logp, dict_label
    return log_unk * len(seg), None

def _penalty(seg: str) -> float:
    if is_english(seg) or is_korean(seg):
        return 0.5 if seg.isalpha() else 1.0
    return len(seg) + (10 if len(seg) <= 2 and not seg.isalpha() else 5)

def _best_path(
        text: str,
        max_len: int,
        log_unk: float,
        length_bonus: float,
        split_penalty: float
    ) -> List[Seg]:
    n = len(text)
    dp: List[Tuple[float, List[Seg]]] = [(-math.inf, []) for _ in range(n + 1)]
    dp[0] = (0.0, [])

    for i in range(1, n + 1):
        for j in range(max(0, i - max_len), i):
            seg = text[j:i]
            logp, label = _segment_logprob(seg, log_unk)
            prev_segs = dp[j][1]
            new_count = len(prev_segs) + 1
            split_cost = split_penalty * new_count
            score = (
                dp[j][0]
                + logp
                - _penalty(seg)
                - split_cost
                + length_bonus * len(seg)
            )
            if score > dp[i][0]:
                dp[i] = (score, prev_segs + [(seg, label)])
    return dp[n][1]

def _merge_unlabeled(segs: List[Seg]) -> List[Seg]:
    merged: List[Seg] = []
    for txt, lab in segs:
        if lab is None and merged and merged[-1][1] is None:
            prev_txt, _ = merged[-1]
            merged[-1] = (prev_txt + txt, None)
        else:
            merged.append((txt, lab))
    return merged

@functools.lru_cache(maxsize=10_000)
def segment_text(
        text: str,
        max_len: int = 20,
        length_bonus: float = 0.1,
        split_penalty: float = 1.0
    ) -> List[Seg]:
    if not text:
        return []

    split_res = split_alpha(text)
    if isinstance(split_res, tuple) and len(split_res) == 2:
        _, parts = split_res
    else:
        parts = split_res

    result: List[Seg] = []
    log_unk = math.log(1e-3)
    for part in parts:
        if not part:
            continue
        if all(is_korean(ch) for ch in part):
            result.append((part, f"H{len(part)}"))
        elif any(ch.isalpha() or ch.isdigit() for ch in part):
            best = _best_path(part, max_len, log_unk, length_bonus, split_penalty)
            for seg, lab in _merge_unlabeled(best):
                result.append((seg, lab))
        else:
            result.append((part, None))
    return result

def detect_dictionary_word(sections: List[Seg]) -> List[Seg]:
    result: List[Seg] = []
    for txt, lab in sections:
        if lab is not None:
            result.append((txt, lab))
        else:
            for s, l in segment_text(txt):
                result.append((s, l))
    return result


if __name__ == "__main__":
    samples = [
        "book",
    ]
    for s in samples:
        print(f"입력: '{s}' -> 결과:", detect_dictionary_word([(s, None)]))
