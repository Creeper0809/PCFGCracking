from collections import Counter

def find_omen_level(omen_trainer, password):
    pw_len = len(password)
    if pw_len < omen_trainer.min_length or pw_len > omen_trainer.max_length:
        return -1
    ngram = omen_trainer.ngram
    try:
        ln_level = omen_trainer.ln_lookup[pw_len - 1][0]

        chunk = password[0:ngram - 1]
        chain_level = omen_trainer.grammar[chunk].start_level

        end_pos = ngram

        while end_pos <= pw_len:
            chunk = password[end_pos - ngram:end_pos]
            chain_level += omen_trainer.grammar[chunk[:-1]].next_letter_candidates[chunk[-1]][0]
            end_pos += 1

        return ln_level + chain_level

    except KeyError:
        return -1


def _rec_calc_keyspace(omen_trainer, level, length, ip):
    if length not in omen_trainer.grammar[ip].keyspace_cache:
        omen_trainer.grammar[ip].keyspace_cache[length] = {}

    if level in omen_trainer.grammar[ip].keyspace_cache[length]:
        return omen_trainer.grammar[ip].keyspace_cache[length][level]

    omen_trainer.grammar[ip].keyspace_cache[length][level] = 0

    if length == 1:
        for last_letter, letter_level in omen_trainer.grammar[ip].next_letter_candidates.items():
            if letter_level[0] == level:
                omen_trainer.grammar[ip].keyspace_cache[length][level] += 1

    else:
        for last_letter, letter_level in omen_trainer.grammar[ip].next_letter_candidates.items():
            if letter_level[0] <= level:
                omen_trainer.grammar[ip].keyspace_cache[length][level] += _rec_calc_keyspace(omen_trainer,
                                                                                                level - letter_level[0],
                                                                                                length - 1,
                                                                                                ip[1:] + last_letter)

    return omen_trainer.grammar[ip].keyspace_cache[length][level]


def calc_omen_keyspace(omen_trainer, max_level=18, max_keyspace=10000000000):
    keyspace = Counter()

    for level in range(1, max_level + 1):

        for ip, ip_info in omen_trainer.grammar.items():
            level_minus_ip = level - ip_info.start_level

            if level_minus_ip > 0:

                for length, length_info in enumerate(omen_trainer.ln_lookup):

                    length += 1

                    if length <= omen_trainer.ngram:
                        continue

                    if length_info[0] <= level_minus_ip:

                        keyspace[level] += _rec_calc_keyspace(
                            omen_trainer,
                            level_minus_ip - length_info[0],
                            length - omen_trainer.ngram + 1,
                            ip)

                        if keyspace[level] > max_keyspace:
                            return keyspace

        print("OMEN Keyspace for Level : " + str(level) + " : " + str(keyspace[level]))

    return keyspace
