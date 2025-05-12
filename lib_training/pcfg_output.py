import os
import codecs
from collections import Counter

def calculate_probabilities(counter: Counter) -> list[tuple]:
    total = sum(counter.values())
    if total == 0:
        return []
    return [(item, count/total) for item, count in counter.most_common()]

def calculate_and_save_counter(path, counter, encoding):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        prob_list = calculate_probabilities(counter)
        with codecs.open(path, 'w', encoding=encoding) as f:
            for item, prob in prob_list:
                f.write(f"{item}\t{prob}\n")
    except Exception as e:
        print(f"[에러] 파일 쓰기 실패: {path} → {e}")
        return False
    return True

def save_indexed_counters(folder, counter_map, encoding):
    try:
        os.makedirs(folder, exist_ok=True)
        # 기존 파일 삭제
        for root, dirs, files in os.walk(folder):
            for fn in files:
                os.unlink(os.path.join(root, fn))
    except Exception as e:
        print(f"[에러] 폴더 초기화 실패: {folder} → {e}")
        return False

    # 각 Counter 저장
    for idx, ctr in counter_map.items():
        filepath = os.path.join(folder, f"{idx}.txt")
        if not calculate_and_save_counter(filepath, ctr, encoding):
            print(f"[에러] Counter 저장 실패: 인덱스={idx}, 폴더={folder}")
            return False
    return True

def save_pcfg_data(base_directory, pcfg_parser, encoding):

    # 폴더 이름과 해당 카운터 맵 매핑
    mappings = [
        ("Keyboard",       pcfg_parser.count_keyboard),
        ("Years",          {'1': pcfg_parser.count_years}),
        ("Alpha",          pcfg_parser.count_alpha),
        ("Capitalization", pcfg_parser.count_alpha_masks),
        ("Digits",         pcfg_parser.count_digits),
        ("Special",        pcfg_parser.count_special),
        ("Korean",         pcfg_parser.count_korean),
    ]
    # 순차적으로 저장
    for folder_name, counter_map in mappings:
        folder = os.path.join(base_directory, folder_name)
        if not save_indexed_counters(folder, counter_map, encoding):
            print(f"[에러] '{folder_name}' 저장 실패")
            return False

    # Grammar 폴더 (ASCII)
    grammar_folder = os.path.join(base_directory, "Grammar")
    grammar_map = {
        'grammar':     pcfg_parser.count_base_structures,
    }
    if not save_indexed_counters(grammar_folder, grammar_map, 'ASCII'):
        print("[에러] 'Grammar' 저장 실패")
        return False

    # Prince 폴더 (ASCII)
    prince_folder = os.path.join(base_directory, "Prince")
    if not save_indexed_counters(prince_folder, {'grammar': pcfg_parser.count_prince}, 'ASCII'):
        print("[에러] 'Prince' 저장 실패")
        return False

    return True
