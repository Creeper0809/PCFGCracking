from collections import Counter

from pcfg_lib.training.detectors.alphabet_detection import detect_alphabet
from pcfg_lib.training.detectors.leet_detection import comb_leets_sections
from pcfg_lib.training.detectors.word_dectection import detect_dictionary_word
from pcfg_lib.training.pcfg.word_trie import WordTrie
from pcfg_lib.training.detectors.digit_detection import digit_detection
from pcfg_lib.training.detectors.keyboard_walk_detection import detect_keyboard_walk
from pcfg_lib.training.detectors.other_detection import other_detection
from pcfg_lib.training.detectors.year_detection import year_detection
from pcfg_lib.training.util.english import get_alphabet_mask
from pcfg_lib.training.util.korean import get_korean_caps_mask


class PCFGParser:
    #=======================================================================================================
    #                                        Initialization Section
    #=======================================================================================================
    def __init__(self, word_trie: WordTrie):
        # word_trie 기반 단어 검출기
        self.word_detector = word_trie

        # 전역 통계 저장용 카운터들
        self.count_keyboard = {}
        self.count_years = Counter()
        self.count_alpha = {}
        self.count_alpha_masks = {}
        self.count_digits = {}
        self.count_special = {}
        self.count_korean = {}
        self.count_base_structures = Counter()
        self.count_prince = Counter()

    #=======================================================================================================
    #                                      Password Parsing Section
    #=======================================================================================================
    def parse(self, password):
        """
        비밀번호를 섹션별로 분할하여 각 탐지기 함수에 전달하고,
        결과 통계를 갱신하며 섹션 리스트를 순차적으로 yield 합니다.
        """
        # 키보드 워크(이동) 패턴 탐지
        raw_section_list, found_walks, keyboard_list = detect_keyboard_walk(password)
        self._update_counter_len_indexed(self.count_keyboard, found_walks)
        # 리트 치환으로 확장된 섹션별 처리
        for section in comb_leets_sections(raw_section_list):
            # 한글/영문 대소문자 섹션 표시
            section = detect_dictionary_word(section)
            # 한글 대문자 마스크
            find_korean_mask = get_korean_caps_mask(section)
            self._update_counter_len_indexed(self.count_alpha_masks, find_korean_mask)

            # 영문 알파벳 탐지
            detect_alphabet(section)

            # 연도(Year) 탐지
            found_year = year_detection(section)
            for year in found_year:
                self.count_years[year] += 1

            # 숫자 탐지
            found_digit = digit_detection(section)
            self._update_counter_len_indexed(self.count_digits, found_digit)

            # 특수문자 및 기타 탐지
            found_special = other_detection(section)
            self._update_counter_len_indexed(self.count_special, found_special)

            # 알파벳 마스크 추가 탐지
            found_alphabet_mask = get_alphabet_mask(section)
            self._update_counter_len_indexed(self.count_alpha_masks, found_alphabet_mask)

            # prince 점수 평가
            self._prince_evaluation(self.count_prince, section)

            # 단어 트라이 학습
            self.word_detector.train_by_section(section)

            # 기본 구조 문자열 생성 및 카운트
            base_structure = self._build_base_structure(section)
            self.count_base_structures[base_structure] += 1

            yield section

    #=======================================================================================================
    #                                   Word Tree Calculation Section
    #=======================================================================================================
    def calculate_word_tree(self):
        """
        학습된 단어 트라이에서 알파벳 및 한글 단어 빈도를 카운터에 저장합니다.
        """
        # 영문 단어 카운트
        for word, count in self.word_detector.get_all_alpha_words():
            self._commit_word(self.count_alpha, word, count)

        # 한글 단어 카운트
        for word, count in self.word_detector.get_all_korean_words():
            self._commit_word(self.count_korean, word, count)

    #=======================================================================================================
    #                                          Util Functions Section
    #=======================================================================================================
    def _build_base_structure(self, section_list) -> str:
        """
        섹션 라벨을 조합하여 기본 구조 문자열을 반환합니다.
        """
        structure = ''
        for string, label in section_list:
            if label is None:
                continue
            structure += label
        return structure

    def _commit_word(self, counter, word, count):
        """
        길이 인덱스별 카운터에 단어와 빈도를 추가합니다.
        """
        try:
            counter[len(word)][word] += count
        except KeyError:
            counter[len(word)] = Counter()
            counter[len(word)][word] = count

    def _prince_evaluation(self, count_prince, section_list):
        """
        section_list의 각 라벨별 prince 점수를 1씩 증가시킵니다.
        """
        for item in section_list:
            count_prince[item[1]] += 1

    def _update_counter_len_indexed(self, input_counter, input_list):
        """
        리스트의 각 항목을 길이별 카운터에 1씩 추가합니다.
        """
        for item in input_list:
            self._commit_word(input_counter, item, 1)
