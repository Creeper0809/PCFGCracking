class Memorizer:
    def __init__(self, max_length):
        self.max_length = max_length
        self.tmto_lookup = [dict() for _ in range(self.max_length + 1)]

    def lookup(self, ip_ngram, length, target_level):
        try:
            return True, self.copy(self.tmto_lookup[length][ip_ngram][target_level])
        except KeyError:
            return False, None

    def update(self, ip_ngram, length, target_level, parse_tree):
        if ip_ngram not in self.tmto_lookup[length]:
            self.tmto_lookup[length][ip_ngram] = {}

        self.tmto_lookup[length][ip_ngram][target_level] = self.copy(parse_tree)

    def copy(self, input_list):
        if input_list:
            return [x[:] for x in input_list]
        return None
