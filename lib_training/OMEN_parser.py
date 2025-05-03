class AlphabetGrammerNode:
    def __init__(self):
        self.count_at_start = 0  # 시작위치에서 등장 횟수
        self.count_at_end = 0  # 마지막 위치에서 등장 횟수
        self.count_in_middle = 0  # 중간 위치에서 등장 횟수
        self.next_letter_candidates = {}  # 다음 알파벳 등장 가능 후보


class AlphabetGrammar:
    def __init__(self, alphabet: str, ngram: int, min_length: int, max_length: int):
        self.alphabet = alphabet
        self.ngram = ngram
        self.grammer = {}
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
            if start_ngram not in self.grammer:
                if not self.is_in_alphabet(start_ngram):
                    continue
                self.grammer[start_ngram] = AlphabetGrammerNode()

            idx: AlphabetGrammerNode = self.grammer[start_ngram]

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

    def is_in_alphabet(self, cur_ngram):
        for letter in cur_ngram:
            if letter not in self.alphabet:
                return False
        return True


class AlphabetCollector:
    def __init__(self, alphabet_size, ngram):
        self.alphabet_size = alphabet_size
        self.ngram = ngram
        self.dictionary = {}

    def process_password(self, password):
        if len(password) < self.ngram:
            return
        for letter in password:
            if letter in ['\t']:
                continue
            if letter in self.dictionary:
                self.dictionary[letter] += 1
            else:
                self.dictionary[letter] = 1
        return

    def get_alphabet(self):
        sorted_alphabet = [(k, self.dictionary[k]) for k in sorted(
            self.dictionary, key=self.dictionary.get, reverse=True)]
        count = 0
        final_alphabet = ''
        for item in sorted_alphabet:
            if count >= self.alphabet_size:
                return final_alphabet
            final_alphabet += item[0]
            count += 1
        return final_alphabet
