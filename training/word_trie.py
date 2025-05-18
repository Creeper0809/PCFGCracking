from dataclasses import dataclass

from training.detectors.alphabet_detection import normalize_leet

@dataclass
class WordNode:
    count = 0
    child = {}
    end_of_word = False


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
        now.end_of_word = True

    def train_by_section(self,section_list):
        for string,label in section_list:
            if label.startswith('H'):
                self._commit_word(self.korean_root_node,string)
            elif label.startswith('A'):
                self._commit_word(self.alpha_root_node,string)
                leet_convert = normalize_leet(string)
                if leet_convert != string:
                    self._commit_word(self.alpha_root_node,leet_convert)

    def train(self, password : str, is_korean :bool,weight :int, make_to_word : bool = False):
        now = self.korean_root_node if is_korean else self.alpha_root_node
        offset = 0 if make_to_word else self.needed_appear
        self._commit_word(now,password,offset)



    def collect_all_words(self, root_node: WordNode, prefix="", min_count=None) -> list[str]:
        result = []

        def dfs(node: WordNode, current: str):
            if node.end_of_word and (min_count is None or node.count >= min_count):
                result.append((current,node.count))
            for ch, child in node.child.items():
                dfs(child, current + ch)

        dfs(root_node, prefix)
        return result

    def get_all_alpha_words(self) -> list[str]:
        return self.collect_all_words(self.alpha_root_node, "", self.needed_appear)

    def get_all_korean_words(self) -> list[str]:
        return self.collect_all_words(self.korean_root_node, "", self.needed_appear)






