import os
import traceback
import sys
from collections import Counter

from lib_training.omen_parser import AlphabetGrammar, find_omen_level
from lib_training.pcfg_parser import PCFGParser
from lib_training.evaluate_password import calc_omen_keyspace
from lib_training.omen_train_data_output import save_omen_rules_to_disk
from lib_training.pcfg_output import save_pcfg_data
from lib_training.train_data_parser import TrainingDataParser
from lib_training.word_trie import WordTrie

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_DATA_DIR = os.path.join(BASE_DIR, "Resource")


def start_train():
    CANDIDATES_PATH = os.path.join(INPUT_DATA_DIR, "korean_password_candidates.txt")

    program_info = {
        'ngram': 3,
        'encoding': 'utf-8',
        'min_length': 4,
        'max_length': 30,
        'alphabet': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.*@-_$#<?',

        # 기본 단어로 취급할 빈도수 << 5번 등장해야 단어로 취급
        'needed_appear': 1,
        # 사전학습 단어의 가중치
        'weight' : 5
    }
    pre_train = TrainingDataParser(
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
        filedir= os.path.join(INPUT_DATA_DIR, "pre_train_english.txt")
    )
    word_trie = WordTrie(needed_appear=program_info['needed_appear'])

    try:
        for word in pre_train.read_password():
            word_trie.train(word,False,program_info['weight'],True)
    except:
        print("기본 단어 학습 중 에러")

    pre_train = TrainingDataParser(
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
        filedir=os.path.join(INPUT_DATA_DIR, "pre_train_korean.txt")
    )
    try:
        for word in pre_train.read_password():
            word_trie.train(word,True,program_info['weight'],True)
    except:
        print("기본 단어 학습 중 에러")

    file_input = TrainingDataParser(
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
        filedir=CANDIDATES_PATH
    )
    omen = AlphabetGrammar(
        ngram=program_info['ngram'],
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
    )
    pcfg_parser = PCFGParser(word_trie)
    trained_count = 0
    try:
        for password in file_input.read_password():
            trained_count += 1
            pcfg_parser.parse(password)
            omen.parse(password)
            if trained_count % 1000 == 0:
                print(str(trained_count // 1000) + '천개')
    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("예외 발생: " + str(msg))
        print("종료 중...")
        return
    omen.apply_smoothing()
    omen_keyspace = calc_omen_keyspace(omen)

    pcfg_parser.caculate_word_tree()

    file_input = TrainingDataParser(
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
        filedir=CANDIDATES_PATH
    )

    omen_level_counter = Counter()

    trained_count = 0
    try:
        for password in file_input.read_password():
            trained_count += 1
            if trained_count % 1000000 == 0:
                print(str(trained_count // 1000000) + ' Million')

            level = find_omen_level(omen, password)
            omen_level_counter[level] += 1

    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("예외 발생: " + str(msg))
        print("종료 중...")
        return

    markov_proportion = 0.6  # 0~1사이 PCFG와 마르코프 패스워드 비율을 어느정도로 맞추겠냐

    if markov_proportion != 1:
        if markov_proportion == 0:
            pcfg_parser.count_base_structures.clear()
            pcfg_parser.count_base_structures["M"] = 1
        else:
            markov_prob = (file_input.num_passwords / markov_proportion) - file_input.num_passwords
            pcfg_parser.count_base_structures['M'] = markov_prob

    base_directory = os.path.join(BASE_DIR,'TrainedSet')

    if not save_omen_rules_to_disk(
            alphabet_grammar=omen,
            omen_keyspace=omen_keyspace,
            omen_levels_count=omen_level_counter,
            num_valid_passwords=file_input.num_passwords,
            base_directory=base_directory,
            program_info=program_info
    ):
        print("OMEN 데이터 저장 중 에러")

    if not save_pcfg_data(
            base_directory=base_directory,
            pcfg_parser=pcfg_parser,
            encoding=program_info['encoding']
    ):
        print("PCFG 데이터 저장 중 에러")


start_train()
