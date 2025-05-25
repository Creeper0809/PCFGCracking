from collections import Counter

from lib.training.pcfg.word_trie import WordTrie
from lib.training.detectors.alphabet_detection import detect_alphabet_mask, expand_all_segmentations
from lib.training.detectors.digit_detection import digit_detection
from lib.training.detectors.keyboard_walk_detection import detect_keyboard_walk
from lib.training.detectors.korean_detection import mark_hn_sections, get_korean_caps_mask
from lib.training.detectors.other_detection import other_detection
from lib.training.detectors.year_detection import year_detection


class PCFGParser:
    def __init__(self,word_trie:WordTrie):
        self.word_detector = word_trie

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
        raw_section_list, found_walks, keyboard_list = detect_keyboard_walk(password)
        self._update_counter_len_indexed(self.count_keyboard,found_walks)

        _, raw_section_list = mark_hn_sections(raw_section_list)

        find_korean_mask = get_korean_caps_mask(raw_section_list)
        self._update_counter_len_indexed(self.count_alpha_masks, find_korean_mask)

        for section in expand_all_segmentations(raw_section_list):

            found_year = year_detection(section)
            for year in found_year:
                self.count_years[year] += 1

            found_degit = digit_detection(section)
            self._update_counter_len_indexed(self.count_digits, found_degit)

            found_special = other_detection(section)
            self._update_counter_len_indexed(self.count_special, found_special)

            found_alphabet_mask = detect_alphabet_mask(section)
            self._update_counter_len_indexed(self.count_alpha_masks, found_alphabet_mask)

            self._prince_evaluation(self.count_prince, section)

            self.word_detector.train_by_section(section)

            base_structure = self._build_base_structure(section)
            self.count_base_structures[base_structure] += 1


    def caculate_word_tree(self):
        for word,count in self.word_detector.get_all_alpha_words():
            self._commit_word(self.count_alpha,word,count)

        for word,count in self.word_detector.get_all_korean_words():
            self._commit_word(self.count_korean,word,count)

    def _build_base_structure(self,section_list) -> str:
        structure = ''
        for string,label in section_list:
            if label is None:
                continue
            structure += label
        return structure

    def _commit_word(self,counter, word, count):
        try:
            counter[len(word)][word] += count
        except:
            counter[len(word)] = Counter()
            counter[len(word)][word] += count

    def _prince_evaluation(self,count_prince, section_list):
        for item in section_list:
            count_prince[item[1]] += 1

    def _update_counter_len_indexed(self, input_counter, input_list):
        for item in input_list:
            self._commit_word(input_counter,item,1)
