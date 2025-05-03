from collections import Counter

from lib_training.detectors.word_trie import WordTrie
from lib_training.detectors.alphabet_detection import detect_alphabet, detect_alphabet_mask
from lib_training.detectors.digit_detection import digit_detection
from lib_training.detectors.keyboard_walk import detect_keyboard_walk
from lib_training.detectors.korean_detection import mark_hn_sections
from lib_training.detectors.other_detection import other_detection
from lib_training.detectors.year_detection import year_detection


class PCFGParser:
    def __init__(self, word_detector : WordTrie):
        self.word_detector = word_detector

        ## 전역 통계 저장용 카운터들
        self.count_keyboard = {}
        self.count_years = Counter()
        self.count_alpha = {}
        self.count_alpha_masks = {}
        self.count_digits = {}
        self.count_special = {}
        self.count_korean = {}
        self.count_base_structures = Counter()
        self.count_prince = Counter()

    def parse(self,password):
        # 키보드 배열 PCFG는 다른 것과 헷갈릴 수 있음으로 제일 먼저 처리
        section_list, found_walks, keyboard_list = detect_keyboard_walk(password)
        self._update_counter_len_indexed(self.count_keyboard,found_walks)

        found_korean,section_list = mark_hn_sections(section_list)
        self._update_counter_len_indexed(self.count_korean,found_korean)

        # 연도는 숫자하고 혼동이 올 수 있으니 미리 처리
        found_year = year_detection(section_list)
        for year in found_year:
            self.count_years[year] += 1

        found_alphabet = detect_alphabet(section_list)
        self._update_counter_len_indexed(self.count_alpha,found_alphabet)

        found_degit =  digit_detection(section_list)
        self._update_counter_len_indexed(self.count_digits,found_degit)

        found_special = other_detection(section_list)
        self._update_counter_len_indexed(self.count_special, found_special)

        found_alphabet_mask = detect_alphabet_mask(section_list)
        self._update_counter_len_indexed(self.count_alpha_masks,found_alphabet_mask)

        self._prince_evaluation(self.count_prince,section_list)

        self.word_detector.train_by_section(section_list)

        base_structure = self._build_base_structure(section_list)
        self.count_base_structures[base_structure] += 1

        print(section_list)
        print(base_structure)


    def _build_base_structure(self,section_list) -> str:
        structure = ''
        for string,label in section_list:
            if label is None:
                continue
            structure += label
        return structure


    def _prince_evaluation(self,count_prince, section_list):
        for item in section_list:
            count_prince[item[1]] += 1

    def _update_counter_len_indexed(self, input_counter, input_list):
        for item in input_list:
            try:
                input_counter[len(item)][item] += 1
            except:
                input_counter[len(item)] = Counter()
                input_counter[len(item)][item] += 1
