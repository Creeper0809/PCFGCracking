import copy
import hashlib
import math
import os
import codecs
from collections import deque
from enum import Enum
from typing import List

import lib.paths
from lib import paths
from lib.guess.omen.markov_guesser import MarkovGuesser
from lib.guess.omen.omen_io import load_omen_rules, load_omen_prob
from lib.guess.omen.memorizer import Memorizer
from lib.guess.pcfg.pcfg_io import load_pcfg_grammar


# =====================
# Data Types
# =====================
class Type(str, Enum):
    EXTENSION     = "extension"
    BASE_PROB     = "base_prob"
    PROB          = "prob"
    REPLACEMENTS  = "replacements"
    TERMINALS     = "terminals"


class Structure:
    """단일 구조(symbol, index)를 표현하는 클래스"""
    def __init__(self, symbol: str, index: int):
        self.symbol = symbol
        self.index  = index


class TreeItem:
    """트리 탐색 시각마다 확률과 구조 목록을 저장하는 노드"""
    def __init__(self):
        self.base_prob  = 1.0
        self.structures: List[Structure] = []
        self.prob       = 0.0


# =====================
# Initialization
# =====================
class PCFGGuesser:
    def __init__(self, config):
        # 출력 관련 초기화
        self.output_filename = None
        self.output_file     = None
        self.print_guess     = print
        self.log             = config["log"]

        # PCFG 문법 로드
        self.grammar, self.base_structure = load_pcfg_grammar(
            db_path=os.path.join(paths.ROOT_PATH, "sqlite3.db")
        )

        # OMEN 룰 및 확률 로드
        self.omen_grammar    = load_omen_rules(db_path=paths.KOREAN_DICT_DB_PATH)
        load_omen_prob(
            dbpath=paths.KOREAN_DICT_DB_PATH,
            grammar=self.grammar
        )
        self.omen_optimizer = Memorizer(max_length=4)
        self.omen_guess_num = 0

        # Attack mode = Markov only 인 경우 기본 구조 변경
        if config["attack_mode"] == 1:
            self.base_structure = [{
                Type.PROB:         1,
                Type.REPLACEMENTS: ["M"]
            }]

        # 해시 비교 설정
        self.hash_algo     = config.get("mode", "md5")
        self.target_hashes = set()
        self.found         = {}

        if config.get("hashfile"):
            with open(config["hashfile"], encoding="utf-8") as f:
                self.target_hashes = {line.strip() for line in f if line.strip()}

        # 최근 추측 보관
        self.recent_guesses = deque(maxlen=10)
        self.print_guess    = self._record_and_compare
        self.made_password  = 0

        # 로깅
        if self.log:
            print("-" * 40)
            print("Loaded PCFG grammar terms:")
            for label, entries in self.grammar.items():
                print(label, entries)
            print("-" * 40)


# =====================
# Guess Output Management
# =====================
    def _record_and_compare(self, guess: str):
        """추측을 기록하고, 해시와 비교하여 일치 시 found에 저장"""
        self.recent_guesses.append(guess)
        digest = getattr(hashlib, self.hash_algo)(guess.encode()).hexdigest()
        if digest in self.target_hashes:
            self.found[digest] = guess
            self.target_hashes.remove(digest)

    def save_to_file(self, filename: str):
        """추측 결과를 파일로 저장하도록 출력 함수 전환"""
        if self.output_file:
            self.output_file.close()
        self.output_filename = filename
        if not filename:
            self.output_file = None
            self.print_guess  = print
            return

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.output_file = codecs.open(filename, 'w', encoding='utf-8')
        self.print_guess = self.write_guess_to_file

    def _compare_and_print(self, guess: str):
        """기존 print_guess 대체용, 파일이 아니라 콘솔 비교 출력"""
        digest = getattr(hashlib, self.hash_algo)(guess.encode()).hexdigest()
        if digest not in self.target_hashes:
            return
        self.found[digest] = guess
        self.target_hashes.remove(digest)

    def write_guess_to_file(self, guess: str):
        """파일 핸들러에 추측을 기록"""
        if not self.output_file:
            return
        self.output_file.write(guess + "\n")

    def shutdown(self):
        """출력 파일이 열려 있으면 닫기"""
        if self.output_file:
            self.output_file.close()


# =====================
# Base Structure Initialization
# =====================
    def initialize_base_structures(self) -> List[TreeItem]:
        """config에 따라 초기 TreeItem 노드 리스트 생성"""
        base_structures: List[TreeItem] = []
        for item in self.base_structure:
            node = TreeItem()
            node.base_prob = item[Type.PROB]
            for repl in item[Type.REPLACEMENTS]:
                idx = 1 if repl == "M" else 0
                node.structures.append(Structure(repl, idx))
            node.prob = self._calc_prob(node.structures, node.base_prob)
            base_structures.append(node)
        return base_structures


# =====================
# Probability Calculation
# =====================
    def _calc_prob(self, structures: List[Structure], base_prob: float) -> float:
        """구조 리스트에 대한 log 확률 계산"""
        total = math.log(base_prob)
        for st in structures:
            sym = st.symbol
            ix  = st.index
            total += math.log(self.grammar[sym][ix][Type.PROB])
        return total


# =====================
# Child Generation
# =====================
    def find_children(self, pt_item: TreeItem) -> List[TreeItem]:
        """현재 TreeItem에서 다음 레벨 자식 노드들 생성"""
        parent_prob       = pt_item.prob
        parent_structures = pt_item.structures
        children: List[TreeItem] = []

        for pos, struct in enumerate(parent_structures):
            sym, idx = struct.symbol, struct.index
            # 더 이상 확장 불가 시 건너뛰기
            if len(self.grammar[sym]) <= idx + 1:
                continue
            # 복사 후 인덱스 증가
            new_structs = copy.copy(parent_structures)
            new_structs[pos] = Structure(sym, idx + 1)
            # 유효성 검사
            if self._is_valid_child(new_structs, pt_item.base_prob, pos, parent_prob):
                child_node = TreeItem()
                child_node.base_prob  = pt_item.base_prob
                child_node.structures = new_structs
                child_node.prob       = self._calc_prob(new_structs, pt_item.base_prob)
                children.append(child_node)
        return children

    def _is_valid_child(self,
                        child: List[Structure],
                        base_prob: float,
                        parent_pos: int,
                        parent_prob: float) -> bool:
        """
        확장된 구조가 parent보다 확률이 떨어지지는 않는지,
        동률 경우에는 순서를 보장하는지 체크
        """
        for pos, st in enumerate(child):
            if pos == parent_pos or st.index == 0:
                continue
            # 한 단계 되돌려서 비교
            tmp = copy.copy(child)
            tmp[pos] = Structure(st.symbol, st.index - 1)
            if self._calc_prob(tmp, base_prob) < parent_prob:
                return False
            if self._calc_prob(tmp, base_prob) == parent_prob and pos < parent_pos:
                return False
        return True


# =====================
# Guess Generation
# =====================
    def guess(self, structures: List[Structure]):
        """외부 호출용: 초기 구조 리스트로부터 재귀 추측 시작"""
        return self._recursive_guesses("", structures)

    def _recursive_guesses(self,
                           current_guess: str,
                           remain_structures: List[Structure],
                           limit=None):
        """
        남은 구조 목록을 순차 처리하며
        완성된 문자열을 print_guess로 출력하거나
        Markov 분기 처리
        """
        # 구조가 없으면 최종 추측 출력
        if not remain_structures:
            self.print_guess(current_guess)
            self.made_password += 1
            return

        base    = remain_structures[0]
        category = base.symbol[0]
        symbol   = base.symbol
        index    = base.index

        # Markov(M) 분기
        if category == 'M':
            level = int(self.grammar[symbol][index][Type.TERMINALS][0])
            markov = MarkovGuesser(self.omen_grammar, level, self.omen_optimizer)
            guess  = markov.next_guess()
            while guess is not None:
                self.print_guess(guess)
                self.made_password += 1
                guess = markov.next_guess()
            return

        # 대소문자 변환(C) 분기
        if category == "C":
            for mask in self.grammar[symbol][index][Type.TERMINALS]:
                length      = len(mask)
                target_word = current_guess[-length:]
                prefix      = current_guess[:-length]
                new_word    = "".join(
                    target_word[i].upper() if mask[i] == "U"
                    else target_word[i].lower()
                    for i in range(length)
                )
                self._recursive_guesses(prefix + new_word,
                                        remain_structures[1:], limit)
            return

        # 일반 터미널 분기
        for terminal in self.grammar[symbol][index][Type.TERMINALS]:
            self._recursive_guesses(current_guess + terminal,
                                    remain_structures[1:], limit)
        return
