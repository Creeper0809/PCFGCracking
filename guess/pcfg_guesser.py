import copy
import hashlib
import math
import os
import codecs
from collections import deque
from enum import Enum
from typing import List

import Constants
from guess.pcfg_io import load_pcfg_data_from_sqlite


class Type(str, Enum):
    EXTENSION = "extension"
    BASE_PROB = "base_prob"
    PROB = "prob"
    REPLACEMENTS = "replacements"
    TERMINALS = "terminals"


class Structure:
    def __init__(self, symbol: str, index: int):
        self.symbol = symbol
        self.index = index


class TreeItem:
    def __init__(self):
        self.base_prob = 1.0
        self.structures = []
        self.prob = 0.0


class PCFGGuesser:
    def __init__(self, config):
        self.output_filename = None
        self.output_file = None
        self.print_guess = print
        self.log = config["log"]
        self.grammar, self.base_structure = load_pcfg_data_from_sqlite(
            db_path= os.path.join(Constants.BASE_PATH,"sqlite3.db")
        )

        self.hash_algo = config.get("mode", "md5")
        self.target_hashes = set()
        self.found = dict()
        if config.get("hashfile"):
            with open(config["hashfile"], encoding="utf-8") as f:
                self.target_hashes = {line.strip() for line in f if line.strip()}


        self.recent_guesses = deque(maxlen=10)
        self.print_guess = self._record_and_compare

        if self.log:
            print("-" * 40)
            print("terminal load...")
            for label, z in self.grammar.items():
                print(label, z)
            print("-" * 40)

    def _record_and_compare(self, guess: str):

        self.recent_guesses.append(guess)

        digest = getattr(hashlib, self.hash_algo)(guess.encode()).hexdigest()

        if digest in self.target_hashes:
            self.found[digest] = guess
            self.target_hashes.remove(digest)

    def save_to_file(self, filename: str):
        if self.output_file:
            self.output_file.close()
        self.output_filename = filename
        if filename:

            os.makedirs(os.path.dirname(filename), exist_ok=True)
            self.output_file = codecs.open(
                filename,
                'w',
                encoding='utf-8'
            )
            self.print_guess = self.write_guess_to_file
        else:
            self.output_file = None
            self.print_guess = print

    def _compare_and_print(self, guess: str):
        #print(guess)

        digest = getattr(hashlib, self.hash_algo)(guess.encode()).hexdigest()
        if digest not in self.target_hashes:
            return

        self.found[digest] = guess
        self.target_hashes.remove(digest)

    def shutdown(self):
        if self.output_file:
            self.output_file.close()

    def write_guess_to_file(self, guess: str):
        if not self.output_file:
            return
        self.output_file.write(guess)
        self.output_file.write("\n")

    def initialize_base_structures(self):
        base_structures = []
        for item in self.base_structure:
            node = TreeItem()
            node.base_prob = item[Type.PROB]
            for replacement in item[Type.REPLACEMENTS]:
                node.structures.append(Structure(replacement, 0))
            node.prob = self._calc_prob(node.structures, node.base_prob)
            base_structures.append(node)
        return base_structures

    def _calc_prob(self, structures, base_prob):
        prob = math.log(base_prob)
        for structure in structures:
            symbol = structure.symbol
            index = structure.index
            prob += math.log(self.grammar[symbol][index][Type.PROB])
        return prob

    def find_children(self, pt_item: TreeItem):
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
                child_node = TreeItem()
                child_node.base_prob = pt_item.base_prob
                child_node.structures = child
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

    def guess(self, structures: List[TreeItem]):
        return self._recursive_guesses("", structures)

    def _recursive_guesses(self, current_guess: str, remain_structures: List[TreeItem], limit=None):
        if not remain_structures:
            self.print_guess(current_guess)
            return 1

        base = remain_structures[0]
        category = base.symbol[0]
        symbol = base.symbol
        index = base.index
        made_password = 0

        if category == "C":
            for mask in self.grammar[symbol][index][Type.TERMINALS]:
                length = len(mask)
                target_word = current_guess[-length:]
                other_word = current_guess[:-length]
                new_word = ''
                for i in range(length):
                    if mask[i] == "U":
                        new_word += target_word[i].upper()
                    else:
                        new_word += target_word[i].lower()
                new_guess = other_word + new_word
                made_password += self._recursive_guesses(new_guess, remain_structures[1:], limit)
            return made_password

        for terminal in self.grammar[symbol][index][Type.TERMINALS]:
            new_guess = current_guess + terminal
            made_password += self._recursive_guesses(new_guess, remain_structures[1:], limit)

        return made_password
