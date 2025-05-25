import math
from typing import Tuple


def smooth_grammar(grammar, ip_total, ep_total):
    level_adjust_factor = {
        'start': 250,
        'middle': 2,
        'end': 250,
    }
    for starting_letters in grammar.keys():
        index = grammar[starting_letters]

        index.start_level = _calc_level(
            index.count_at_start, ip_total, level_adjust_factor['start']
        )

        index.end_level = _calc_level(
            index.count_at_end, ep_total, level_adjust_factor['end']
        )

        for cond_prob in index.next_letter_candidates:
            cp_count = index.next_letter_candidates[cond_prob]
            level = _calc_level(
                cp_count, index.count_in_middle, level_adjust_factor['middle']
            )
            index.next_letter_candidates[cond_prob] = (level, cp_count)


def smooth_length(ln_lookup, ln_counter, max_level=10):
    for length, count in enumerate(ln_lookup):
        try:
            level = _calc_level(count, ln_counter, 1)
            ln_lookup[length] = (level, count)
        except ZeroDivisionError:
            ln_lookup[length] = (max_level, 0)


def _calc_level(base_count, total_count, level_adjust_factor, max_level=10):

    probi = base_count / total_count
    probi *= level_adjust_factor
    probi += 1e-11

    level = math.floor(-math.log(probi))

    if level < 0:
        level = 0
    elif level > max_level:
        level = max_level

    return level
