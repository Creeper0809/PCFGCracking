import os
import traceback
import sys
from collections import Counter

import Constants
from training.omen.omen_parser import AlphabetGrammar, find_omen_level
from training.pcfg.pcfg_parser import PCFGParser
from training.omen.evaluate_password import calc_omen_keyspace
from training.omen.omen_train_data_output import save_omen_rules_to_disk
from training.pcfg.pcfg_output import save_pcfg_data
from training.io.train_data_parser import TrainingDataParser
from training.pcfg.word_trie import WordTrie

def start_train():
    #CANDIDATES_PATH = os.path.join(Constants.TRAINING_DATA_PATH, "korean_password_candidates.txt")
    CANDIDATES_PATH = os.path.join(Constants.TRAINING_DATA_PATH, "test.txt")

    program_info = {
        'ngram': 3,
        'encoding': 'utf-8',
        'min_length': 4,
        'max_length': 30,
        'alphabet': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.*@-_$#<?',

        # 기본 단어로 취급할 빈도수 << 5번 등장해야 단어로 취급
        'needed_appear': 1,
        # 사전학습 단어의 가중치 학습시 needed_appear * weight 만큼 나온걸로 취급
        'weight' : 5
    }
    pre_train = TrainingDataParser(
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
        filedir= os.path.join(Constants.TRAINING_DATA_PATH, "pre_train_english.txt")
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
        filedir=os.path.join(Constants.TRAINING_DATA_PATH, "pre_train_korean.txt")
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
            print(password)
            trained_count += 1
            pcfg_parser.parse(password)
            omen.parse(password)
            print("-"*40)
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

    markov_proportion = 0

    if markov_proportion != 0:
        if markov_proportion == 1:
            pcfg_parser.count_base_structures.clear()
            pcfg_parser.count_base_structures["M"] = 1
        else:
            markov_prob = (file_input.num_passwords / markov_proportion) - file_input.num_passwords
            pcfg_parser.count_base_structures['M'] = markov_prob

    base_directory = Constants.TRAINED_DATA_PATH

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
