class WordNode:
    def __init__(self):
        self.count = 0
        self.child = {}
        self.end_of_word = False

class WordTrie:
    def __init__(self,needed_appear : int):
        self.needed_appear = needed_appear
        self.korean_root_node = WordNode()
        self.alpha_root_node = WordNode()

    def _commit_word(self,root_node : WordNode, string : str, offset : int = 0):
        now = root_node
        for char in string:
            if char not in now.child:
                now.child[char] = WordNode()
            now = now.child[char]
        now.count += 1 + offset

    def train_by_section(self,section_list):
        for string,label in section_list:
            if label.startswith('H'):
                self._commit_word(self.korean_root_node,string)
            elif label.startswith('A'):
                self._commit_word(self.alpha_root_node,string)

    def train(self, password : str, is_korean :bool, make_to_word : bool = False):
        now = self.korean_root_node if is_korean else self.alpha_root_node
        offset = 0 if make_to_word else self.needed_appear
        self._commit_word(now,password,offset)






