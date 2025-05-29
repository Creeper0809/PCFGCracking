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
        self.grammar, self.base_structure = load_pcfg_grammar(
            db_path= os.path.join(paths.ROOT_PATH, "sqlite3.db")
        )

        self.omen_grammar = load_omen_rules(
            db_path= paths.KOREAN_DICT_DB_PATH
        )
        load_omen_prob(
            dbpath= paths.KOREAN_DICT_DB_PATH,
            grammar=self.grammar)
        self.omen_optimizer = Memorizer(max_length=4)
        self.omen_guess_num = 0

        if config["attack_mode"] == 1:
            self.base_structure = [
                {
                    Type.PROB: 1,
                    Type.REPLACEMENTS: ["M"]
                }
            ]

        self.hash_algo = config.get("mode", "md5")
        self.target_hashes = set()
        self.found = dict()
        if config.get("hashfile"):
            with open(config["hashfile"], encoding="utf-8") as f:
                self.target_hashes = {line.strip() for line in f if line.strip()}


        self.recent_guesses = deque(maxlen=10)
        self.print_guess = self._record_and_compare
        self.made_password = 0
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
        if not filename:
            self.output_file = None
            self.print_guess = print
            return

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.output_file = codecs.open(
            filename,
            'w',
            encoding='utf-8'
        )
        self.print_guess = self.write_guess_to_file


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
                if replacement != "M":
                    node.structures.append(Structure(replacement, 0))
                else:
                    node.structures.append(Structure(replacement, 1))
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

    def guess(self, structures: List[Structure]):
        return self._recursive_guesses("", structures)

    def _recursive_guesses(self, current_guess: str, remain_structures: List[Structure], limit=None):
        if not remain_structures:
            self.print_guess(current_guess)
            self.made_password += 1
            return

        base : Structure = remain_structures[0]
        category = base.symbol[0]
        symbol = base.symbol
        index = base.index

        if category == 'M':
            level = int(self.grammar[symbol][index][Type.TERMINALS][0])
            markov_cracker = MarkovGuesser(self.omen_grammar, level, self.omen_optimizer)
            self.omen_guess_num = 0

            guess = markov_cracker.next_guess()

            while guess is not None:
                self.print_guess(guess)
                self.made_password += 1
                self.omen_guess_num += 1
                guess = markov_cracker.next_guess()
            return

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
                self._recursive_guesses(new_guess, remain_structures[1:], limit)
            return

        for terminal in self.grammar[symbol][index][Type.TERMINALS]:
            new_guess = current_guess + terminal
            self._recursive_guesses(new_guess, remain_structures[1:], limit)

        return
