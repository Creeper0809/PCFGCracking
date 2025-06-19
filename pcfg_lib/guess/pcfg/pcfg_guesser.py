# pcfg_guesser.py
import copy
import math
import os
from enum import Enum
from typing import Generator, List

import pcfg_lib.paths
from pcfg_lib import paths
from pcfg_lib.guess.omen.markov_guesser import MarkovGuesser
from pcfg_lib.guess.omen.omen_io import load_omen_rules, load_omen_prob
from pcfg_lib.guess.omen.memorizer import Memorizer
from pcfg_lib.guess.pcfg.pcfg_io import load_pcfg_grammar


# =====================
# Data Types
# =====================
class Type(str, Enum):
    EXTENSION = "extension"
    BASE_PROB = "base_prob"
    PROB = "prob"
    REPLACEMENTS = "replacements"
    TERMINALS = "terminals"
    LENGTHS = "lengths"


class Structure:
    """단일 구조(symbol, index)를 표현하는 클래스"""
    def __init__(self, symbol: str, index: int,start:int, end:int):
        self.symbol = symbol
        self.index = index
        self.start = start
        self.end = end

    def serialize(self):
        return {
            "symbol": self.symbol,
            "index": self.index,
            "start": self.start,
            "end": self.end
        }

    def __str__(self):
        return " ".join([str(self.symbol), str(self.index), str(self.start), str(self.end)])

class TreeItem:
    """트리 탐색 시점마다 확률과 구조 목록을 저장하는 노드"""
    def __init__(self):
        self.base_prob: float = 1.0
        self.structures: List[Structure] = []
        self.prob: float = 0.0
        self.total_candidate = 0


# =====================
# PCFGGuesser: 순수 패스워드 생성기
# =====================
class PCFGGuesser:
    def __init__(self, config):
        self.log = config.get("log", False)
        # PCFG 문법 로드
        self.grammar, self.base_structure = load_pcfg_grammar(
            db_path=os.path.join(paths.BASE_PATH, "sqlite3.db")
        )
        # OMEN 룰 및 확률 로드
        self.omen_grammar = load_omen_rules(db_path=paths.KOREAN_DICT_DB_PATH)
        load_omen_prob(
            dbpath=paths.KOREAN_DICT_DB_PATH,
            grammar=self.grammar
        )
        self.omen_optimizer = Memorizer(max_length=4)
        # Markov only 모드
        if config.get("attack_mode",0) == 1:
            self.base_structure = [{Type.PROB: 1.0, Type.REPLACEMENTS: ["M"]}]
        if self.log:
            print("[PCFGGuesser] Loaded grammar entries:")
            for lbl, ents in self.grammar.items(): print(lbl, ents)
        self.made_password: int = 0

        self.is_exit = False

    def initialize_base_structures(self) -> List[TreeItem]:
        items: List[TreeItem] = []
        for entry in self.base_structure:
            node = TreeItem()
            node.base_prob = float(entry[Type.PROB])
            for sym in entry[Type.REPLACEMENTS]:
                idx = 1 if sym == "M" else 0
                node.structures.append(Structure(sym, idx,0,self.grammar[sym][idx][Type.LENGTHS]))
            node.prob = self._calc_prob(node.structures, node.base_prob)
            node.total_candidate = self._calc_total_candidate(node)
            items.append(node)
        return items

    def _calc_prob(self, structures: List[Structure], base_prob: float) -> float:
        # log 확률 합산
        total = math.log(base_prob)
        for st in structures:
            total += math.log(self.grammar[st.symbol][st.index][Type.PROB])
        return total

    def _calc_total_candidate(self,node):
        total = 1
        for st in node.structures:
            total *= self.grammar[st.symbol][st.index][Type.LENGTHS]
        return total

    def find_children(self, parent: TreeItem) -> List[TreeItem]:
        children: List[TreeItem] = []
        parent_prob = parent.prob
        for pos, struct in enumerate(parent.structures):
            sym, idx = struct.symbol, struct.index
            # 더 이상 확장 없음
            if idx + 1 >= len(self.grammar[sym]):
                continue
            new_structs = copy.copy(parent.structures)
            new_structs[pos] = Structure(sym, idx + 1,0,self.grammar[sym][idx + 1][Type.LENGTHS])
            if self._is_valid_child(new_structs, parent.base_prob, pos, parent_prob):
                node = TreeItem()
                node.base_prob = parent.base_prob
                node.structures = new_structs
                node.prob = self._calc_prob(new_structs, parent.base_prob)
                node.total_candidate = self._calc_total_candidate(node)
                children.append(node)
        return children

    def _is_valid_child(self, child: List[Structure], base_prob: float,
                        parent_pos: int, parent_prob: float) -> bool:
        for pos, st in enumerate(child):
            if pos == parent_pos or st.index == 0:
                continue
            tmp = copy.copy(child)
            tmp[pos] = Structure(st.symbol, st.index - 1,0,self.grammar[st.symbol][st.index - 1][Type.LENGTHS])
            if self._calc_prob(tmp, base_prob) < parent_prob:
                return False
            if self._calc_prob(tmp, base_prob) == parent_prob and pos < parent_pos:
                return False
        return True

    def split_structures(self, node, value):
        splited_structures = [[] for _ in range(value)]

        for st in node.structures:
            total = self.grammar[st.symbol][st.index][Type.LENGTHS]

            # chunk 크기보다 총 개수를 우선 고려
            chunk_size = math.ceil(total / value)

            for i in range(value):
                start = i * chunk_size
                end = min((i + 1) * chunk_size, total)

                if start >= end:
                    continue  # 범위가 없으면 무시

                splited_structures[i].append(
                    Structure(st.symbol, st.index, start, end)
                )

        return splited_structures

    def guess(self, structures: List[Structure]) -> Generator[str, None, None]:
        """패스워드 제너레이터: 하나씩 yield"""
        self.made_password = 0
        yield from self._recursive_gen("", structures)

    def _recursive_gen(self, current: str,
                       structures: List[Structure]) -> Generator[str, None, None]:
        if not structures:
            self.made_password += 1
            yield current
            return

        if self.is_exit:
            return

        base = structures[0]
        cat = base.symbol[0]
        # Markov
        if cat == 'M':
            level = int(self.grammar[base.symbol][base.index][Type.TERMINALS][0])
            markov = MarkovGuesser(self.omen_grammar, level, self.omen_optimizer)
            nxt = markov.next_guess()
            while nxt is not None and not self.is_exit:
                self.made_password += 1
                yield nxt
                nxt = markov.next_guess()
            return
        # Case transform
        if cat == 'C':
            for i in range(base.start,base.end):
                mask = self.grammar[base.symbol][base.index][Type.TERMINALS][i]
                length = len(mask)
                prefix = current[:-length]
                tail = current[-length:]
                new = ''.join(
                    tail[i].upper() if mask[i] == 'U' else tail[i].lower()
                    for i in range(length)
                )
                yield from self._recursive_gen(prefix + new, structures[1:])
            return
        # Terminal
        for i in range(base.start,base.end):
            term = self.grammar[base.symbol][base.index][Type.TERMINALS][i]
            yield from self._recursive_gen(current + term, structures[1:])