import os
import traceback
import sys

from lib_training.OMEN_parser import AlphabetGrammar, AlphabetCollector
from lib_training.PCFG_parser import PCFGParser
from lib_training.detectors.word_trie import WordTrie
from lib_training.evaluate_password import calc_omen_keyspace
from lib_training.train_data_parser import TrainingDataParser

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_DATA_DIR = os.path.join(BASE_DIR, "Resource")

def start_train():
    CANDIDATES_PATH = os.path.join(INPUT_DATA_DIR, "korean_password_candidates.txt")

    min_length = 4
    max_length = 30
    ngram = 3

    file_input = TrainingDataParser(
        min_length=min_length,
        max_length=max_length,
        filedir=CANDIDATES_PATH
    )
    omen = AlphabetGrammar(
        ngram=ngram,
        min_length = min_length,
        max_length = max_length,
    )
    word_detector = WordTrie(
        needed_appear=5
    )
    pcfg_parser = PCFGParser(
        word_detector=word_detector
    )
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

    print(omen_keyspace)

start_train()