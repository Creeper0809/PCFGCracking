import sys

from lib.training.util.english import normalize_leet

sys.setrecursionlimit(10000000)

class WordNode:
    def __init__(self):
        self.count = 0
        self.child = {}
        self.end_of_word = False

class WordTrie:
    #=======================================================================================================
    #                                         Initialization Section
    #=======================================================================================================
    def __init__(self, needed_appear: int):
        # 단어를 유효한 것으로 간주하기 위한 최소 등장 횟수
        self.needed_appear = needed_appear
        # 한글 단어를 저장하는 Trie의 루트 노드
        self.korean_root_node = WordNode()
        # 알파벳 단어를 저장하는 Trie의 루트 노드
        self.alpha_root_node = WordNode()

    #=======================================================================================================
    #                                 Internal Word Commit Method
    #=======================================================================================================
    def _commit_word(self, root_node: WordNode, string: str, offset: int = 0):
        # 문자열을 소문자로 변환하여 Trie에 삽입 << 대문자 마스킹은 이미 되었기 때문
        node = root_node
        string = string.lower()
        for char in string:
            if char not in node.child:
                node.child[char] = WordNode()
            node = node.child[char]
        node.count += 1 + offset
        node.end_of_word = True

    #=======================================================================================================
    #                                        Training Method
    #========================================================================================================
    def train_by_section(self, section_list : list):
        # 각 섹션의 라벨에 따라 한글/영문 Trie에 학습
        for string, label in section_list:
            if label.startswith('H'):
                # 한글 단어 추가
                self._commit_word(self.korean_root_node, string)
            elif label.startswith('A'):
                # 알파벳 단어 추가
                self._commit_word(self.alpha_root_node, string)
                # Leet 변환 문자열도 추가 학습
                leet_str = normalize_leet(string)
                if leet_str != string:
                    self._commit_word(self.alpha_root_node, leet_str)

    def train(self, password: str, is_korean: bool, weight: int, make_to_word: bool = False):
        # 단일 비밀번호를 한글/영문 Trie에 학습
        node = self.korean_root_node if is_korean else self.alpha_root_node
        offset = 0 if make_to_word else self.needed_appear
        self._commit_word(node, password, offset)

    #=======================================================================================================
    #                           Word Collection and Lookup Methods
    #=======================================================================================================
    def collect_all_words(self, root_node: WordNode, prefix: str = "", min_count: int = None) -> list:
        # DFS를 통해 모든 단어와 등장 횟수를 결과 리스트로 반환
        result = []
        def dfs(node: WordNode, current: str):
            if node.end_of_word and (min_count is None or node.count >= min_count):
                result.append((current, node.count))
            for ch, child in node.child.items():
                dfs(child, current + ch)
        dfs(root_node, prefix)
        return result

    def get_all_alpha_words(self) -> list:
        # 알파벳 Trie에서 필요 횟수 이상 등장한 단어 반환
        return self.collect_all_words(self.alpha_root_node, "", self.needed_appear)

    def get_all_korean_words(self) -> list:
        # 한글 Trie에서 필요 횟수 이상 등장한 단어 반환
        return self.collect_all_words(self.korean_root_node, "", self.needed_appear)
