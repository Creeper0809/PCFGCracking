
import os
import configparser
import codecs
from collections import Counter

from training.train_output import make_sure_path_exists


def save_omen_rules_to_disk(
    alphabet_grammar,
    omen_keyspace,
    omen_levels_count,
    num_valid_passwords,
    base_directory,
    program_info
):
    encoding = program_info['encoding']
    omen_dir = os.path.join(base_directory, "OMEN")
    try:
        make_sure_path_exists(omen_dir)
    except Exception as e:
        print("OMEN 디렉토리 만드는 중 에러:", e)
        return False

    # 1) 접두사 start_level 집계
    full_path = os.path.join(omen_dir, "Prefix.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as f:
            for prefix, node in alphabet_grammar.grammar.items():
                f.write(f"{node.start_level}\t{prefix}\n")
    except Exception as e:
        print("접두사 레벨 생성 중 에러:", e)
        return False

    # 2) 접미사 end_level 집계
    full_path = os.path.join(omen_dir, "Suffix.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as f:
            for prefix, node in alphabet_grammar.grammar.items():
                f.write(f"{node.end_level}\t{prefix}\n")
    except Exception as e:
        print("접미사 생성 중 에러:", e)
        return False

    # 3) CP.level: conditional probabilities
    full_path = os.path.join(omen_dir, "conditional_probabilities.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as f:
            for prefix, node in alphabet_grammar.grammar.items():
                for next_char, level_info in node.next_letter_candidates.items():
                    level = level_info[0] if isinstance(level_info, (list, tuple)) else level_info
                    f.write(f"{level}\t{prefix}{next_char}\n")
    except Exception as e:
        print("중간 레벨 생성 중 에러:", e)
        return False

    # 4) Length.level: 길이 기반 레벨
    full_path = os.path.join(omen_dir, "Length.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as f:
            # smoothing 후 ln_lookup는 [ [level,count], ... ] 형태
            for entry in alphabet_grammar.ln_lookup:
                level = entry[0] if isinstance(entry, (list, tuple)) else entry
                f.write(f"{level}\n")
    except Exception as e:
        print("LN.level 작성 중 에러:", e)
        return False

    # 5) config.txt: ngram, encoding
    if not _save_config(os.path.join(omen_dir, "config.txt"),
                        program_info['ngram'],
                        program_info['encoding']):
        return False

    # 6) alphabet.txt: 알파벳 목록
    if not _save_alphabet(os.path.join(omen_dir, "alphabet.txt"),
                          program_info['alphabet'],
                          encoding):
        return False

    # 7) omen_keyspace.txt: 레벨별 keyspace
    full_path = os.path.join(omen_dir, "omen_keyspace.txt")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as f:
            for lvl, ks in reversed(omen_keyspace.most_common()):
                f.write(f"{lvl}\t{ks}\n")
    except Exception as e:
        print("omen_keyspace.txt 작성 중 에러:", e)
        return False

    # 8) omen_pws_per_level.txt: 레벨별 크랙된 비밀번호 수
    full_path = os.path.join(omen_dir, "omen_pws_per_level.txt")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as f:
            for lvl, cnt in omen_levels_count.most_common():
                f.write(f"{lvl}\t{cnt}\n")
    except Exception as e:
        print("omen_pws_per_level.txt 작성 중 에러:", e)
        return False

    # 9) pcfg_omen_prob.txt: 레벨별 추정 확률 계산 및 저장
    full_path = os.path.join(omen_dir, "pcfg_omen_prob.txt")
    try:
        pcfg_omen_prob = Counter()
        for lvl, ks in omen_keyspace.items():
            if ks == 0:
                continue
            num_inst = omen_levels_count.get(lvl, 0)
            pct = num_inst / num_valid_passwords
            pcfg_omen_prob[lvl] = pct / ks

        with codecs.open(full_path, 'w', encoding=encoding) as f:
            for lvl, prob in pcfg_omen_prob.most_common():
                f.write(f"{lvl}\t{prob}\n")
    except Exception as e:
        print("omen_prob.txt 작성 중 에러:", e)
        return False

    return True


def _save_config(path, ngram, encoding):
    config = configparser.ConfigParser()
    config.add_section("training_settings")
    config.set("training_settings", "ngram", str(ngram))
    config.set("training_settings", "encoding", encoding)
    try:
        with open(path, 'w') as cfgf:
            config.write(cfgf)
    except Exception as e:
        print("config.txt 작성 중 에러:", e)
        return False
    return True


def _save_alphabet(path, alphabet, encoding):
    try:
        with codecs.open(path, 'w', encoding=encoding) as af:
            for ch in alphabet:
                af.write(ch + "\n")
    except Exception as e:
        print("alphabet.txt 작성 중 에러:", e)
        return False
    return True
