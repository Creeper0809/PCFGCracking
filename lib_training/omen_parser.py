from lib_training import smoothing


class AlphabetGrammerNode:
    def __init__(self):
        self.count_at_start = 0  # 시작위치에서 등장 횟수
        self.count_at_end = 0  # 마지막 위치에서 등장 횟수
        self.count_in_middle = 0  # 중간 위치에서 등장 횟수
        self.next_letter_candidates = {}  # 다음 알파벳 등장 가능 후보

        self.start_level = 0
        self.end_level = 0
        self.keyspace_cache = {}


class AlphabetGrammar:
    def __init__(self, ngram: int, min_length: int, max_length: int):
        self.ngram = ngram
        self.grammar = {}
        self.min_length = min_length
        self.max_length = max_length

        self.count_at_start = 0
        self.count_at_end = 0
        self.count_in_middle = 0

        # 전체 길이 카운터
        self.ln_counter = 0

        # 길이 기반 테이블 (인덱스를 사용하여 길이 기반 조회를 빠르게 함)
        self.ln_lookup = [0] * self.max_length

    def parse(self, password: str):
        # 길이 통계 업데이트
        password_length = len(password)
        self.ln_lookup[password_length - 1] += 1
        self.ln_counter += 1

        for i in range(password_length - self.ngram + 2):
            start_ngram = password[i: i + self.ngram - 1]
            if start_ngram not in self.grammar:
                self.grammar[start_ngram] = AlphabetGrammerNode()

            idx: AlphabetGrammerNode = self.grammar[start_ngram]

            if i == 0:
                idx.count_at_start += 1
                self.count_at_start += 1

            if i != password_length - (self.ngram - 1):
                end_ngram = password[i + self.ngram - 1]
                idx.count_in_middle += 1
                idx.next_letter_candidates[end_ngram] = idx.next_letter_candidates.get(end_ngram, 0) + 1
            else:
                idx.count_at_end += 1
                self.count_at_end += 1

    def apply_smoothing(self):
        smoothing.smooth_length(self.ln_lookup, self.ln_counter)
        smoothing.smooth_grammar(self.grammar, self.count_at_start, self.count_at_end)

def find_omen_level(omen_trainer, password):
    pw_len = len(password)
    if pw_len < omen_trainer.min_length or pw_len > omen_trainer.max_length:
        return -1

    ngram = omen_trainer.ngram

    try:

        ln_level = omen_trainer.ln_lookup[pw_len - 1][0]

        chunk = password[0:ngram-1]
        chain_level = omen_trainer.grammar[chunk].start_level

        end_pos = ngram

        while end_pos <= pw_len:
            chunk = password[end_pos - ngram:end_pos]
            chain_level += omen_trainer.grammar[chunk[:-1]].next_letter_candidates[chunk[-1]][0]
            end_pos += 1

        return ln_level + chain_level

    except KeyError:
        return -1


