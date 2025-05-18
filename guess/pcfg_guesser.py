import copy
import math
import os
from dataclasses import dataclass
from enum import Enum
from typing import List

from guess.pcfg_io import load_pcfg_data

class Type(str,Enum):
    EXTENSION = "extension"
    BASE_PROB = "base_prob"
    PROB = "prob"
    REPLACEMENTS = "replacements"
    TERMINALS = "terminals"

@dataclass
class Structure:
    symbol: str
    index: int

@dataclass
class TreeItem:
    base_prob: float
    structures: List[Structure]
    prob: float = 0.0


class PCFGGuesser:

    def __init__(self):
        here = os.path.dirname(__file__)
        trainedset_dir = os.path.abspath(
            os.path.join(here, '..', 'TrainedSet')
        )
        self.grammar, self.base_structure = load_pcfg_data(
            base_directory=trainedset_dir,
            encoding = "utf-8"
        )


    def initialize_base_structures(self):
        pt_list = []

        for item in self.base_structure:
            node = TreeItem(item[Type.PROB], [])

            for replacement in item[Type.REPLACEMENTS]:
                node.structures.append(Structure(replacement, 0))

            node.prob = self._calc_prob(node.structures, node.base_prob)
            pt_list.append(node)

        return pt_list

    def _calc_prob(self, structures, base_prob):
        prob = math.log(base_prob)
        for structure in structures:
            symbol = structure.symbol
            index = structure.index

            prob += math.log(self.grammar[symbol][index][Type.PROB])
        return prob

    def find_children(self, pt_item : TreeItem):
        parent_prob = pt_item.prob
        parent_structures = pt_item.structures

        children_list = []

        for pos, item in enumerate(parent_structures):

            parent_type = item.symbol
            parent_index = item.index

            if len(self.grammar[parent_type]) == parent_index + 1:
                continue

            child = copy.copy(parent_structures)
            child[pos] = Structure(child[pos].symbol, child[pos].index + 1)

            if self._is_valid_child(child, pt_item.base_prob, pos, parent_prob):
                child_node = TreeItem(pt_item.base_prob, child)
                child_node.prob = self._calc_prob(child, pt_item.base_prob)
                children_list.append(child_node)

        return children_list

    def _is_valid_child(self, child, base_prob, parent_pos, parent_prob):
        for pos, item in enumerate(child):

            if pos == parent_pos:
                continue

            if item.index == 0:
                continue

            new_parent = copy.copy(child)
            new_parent[pos] = Structure(new_parent[pos].symbol, new_parent[pos].index - 1)

            new_parent_prob = self._calc_prob(new_parent, base_prob)

            if new_parent_prob < parent_prob:
                return False
            elif new_parent_prob == parent_prob:
                if pos < parent_pos:
                    return False
        return True

    def guess(self, structures):
        return self._recursive_guesses("", structures)

    def _recursive_guesses(self,current_guess, structures,limit = None):

        made_password = 0

        if len(structures) == 0:
            print(current_guess)
            return 1

        base = structures[0]

        category = base.symbol[0]
        symbol = base.symbol
        index = base.index

        for terminal in self.grammar[symbol][index][Type.TERMINALS]:
            new_guess = current_guess + terminal

            made_password += self._recursive_guesses(new_guess, structures[1:],limit)

        return made_password