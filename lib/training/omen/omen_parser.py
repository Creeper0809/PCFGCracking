from lib.training.omen import smoothing


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

    def parse(self, password: str, weight : int = 1):
        password_length = len(password)
        self.ln_lookup[password_length - 1] += weight
        self.ln_counter += weight

        for i in range(password_length - self.ngram + 2):
            start_ngram = password[i: i + self.ngram - 1]
            if start_ngram not in self.grammar:
                self.grammar[start_ngram] = AlphabetGrammerNode()

            idx: AlphabetGrammerNode = self.grammar[start_ngram]

            if i == 0:
                idx.count_at_start += weight
                self.count_at_start += weight

            if i != password_length - (self.ngram - 1):
                end_ngram = password[i + self.ngram - 1]
                idx.count_in_middle += weight
                idx.next_letter_candidates[end_ngram] = idx.next_letter_candidates.get(end_ngram, 0) + weight
            else:
                idx.count_at_end += weight
                self.count_at_end += weight

    def apply_smoothing(self):
        smoothing.smooth_length(self.ln_lookup, self.ln_counter)
        smoothing.smooth_grammar(self.grammar, self.count_at_start, self.count_at_end)


