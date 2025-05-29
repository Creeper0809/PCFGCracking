import sys
import pickle  # 세션 저장을 위해 사용됨

# 로컬 모듈 임포트
from .guess_structure import GuessStructure


class MarkovGuesser:
    def __init__(self, grammar, target_level=1, memorizer=None):
        # 규칙 세트 저장
        self.grammar = grammar

        # 최적화기 저장
        self.memorizer = memorizer

        # 항목이 가질 수 있는 최대 레벨
        self.max_level = grammar['max_level']

        # 초기 확률 항목의 길이. 매번 ngram - 1을 계산하지 않기 위해 저장함
        self.length_ip = grammar['ngram'] - 1

        # 유효한 첫 번째 IP 포인터
        self.start_ip = self._find_first_object(self.grammar['ip'])

        # 유효한 첫 번째 길이 포인터
        self.start_length = self._find_first_object(self.grammar['ln'])

        # 목표로 하는 전체 레벨
        self.target_level = target_level

        # 현재 길이 포인터
        self.cur_len = None

        # 현재 IP 포인터
        self.cur_ip = None

        # 현재 추측 구조
        self.cur_guess = None

    def _find_first_object(self, lookup_table):
        for level in range(0, self.max_level):
            if len(lookup_table[level]) != 0:
                return level
        print("IP 또는 LN이 유효하지 않습니다. GitHub 페이지에 버그를 제보해 주세요.", file=sys.stderr)
        raise Exception

    def next_guess(self):
        if self.cur_guess is None:
            self.cur_len = [self.start_length, 0]
            self.cur_ip  = [self.start_ip, 0]
            self.cur_guess = GuessStructure(
                max_level=self.max_level,
                cp=self.grammar['cp'],
                ip=self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                cp_length=self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                target_level=self.target_level - self.cur_len[0] - self.cur_ip[0],
                memorizer=self.memorizer,
            )
        guess = self.cur_guess.next_guess()
        while guess is None:
            if not self._increase_ip_for_target(working_target=self.target_level - self.cur_len[0]):
                if not self._increase_len_for_target():
                    self.cur_guess = None
                    return None
            guess = self.cur_guess.next_guess()
        return guess

    def _increase_len_for_target(self):
        level = self.cur_len[0]
        index = self.cur_len[1] + 1

        ln = self.grammar['ln']

        # 남아 있는 유효한 모든 레벨 순회
        while level <= self.max_level:

            # 현재 레벨에서 길이 옵션이 존재하는지 확인
            size = len(ln[level])
            if size > index:
                # 새로운 길이 포인터 저장
                self.cur_len = [level, index]

                # 현재 IP 초기화
                self.cur_ip = [self.start_ip, 0]

                # 현재 추측 구조 재설정
                self.cur_guess = GuessStructure(
                    cp=self.grammar['cp'],
                    max_level=self.max_level,
                    ip=self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                    cp_length=self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                    target_level=self.target_level - self.cur_len[0] - self.cur_ip[0],
                    memorizer=self.memorizer,
                )
                return True

            # 현재 레벨에서 유효한 항목이 없을 경우, 다음 레벨 확인
            level += 1
            index = 0
            if level > self.max_level or level > self.target_level:
                return False

    def _increase_ip_for_target(self, working_target=0):
        level = self.cur_ip[0]
        index = self.cur_ip[1] + 1

        ip = self.grammar['ip']

        # 남아 있는 유효한 모든 레벨 순회
        while level <= self.max_level:

            # 현재 레벨에서 IP 옵션이 존재하는지 확인
            size = len(ip[level])
            if size > index:
                # 새로운 IP 포인터 저장
                self.cur_ip = [level, index]

                # 현재 추측 구조 재설정
                self.cur_guess = GuessStructure(
                    cp=self.grammar['cp'],
                    max_level=self.max_level,
                    ip=self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                    cp_length=self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                    target_level=self.target_level - self.cur_len[0] - self.cur_ip[0],
                    memorizer=self.memorizer,
                )
                return True

            # 현재 레벨에서 유효한 항목이 없을 경우, 다음 레벨 확인
            level += 1
            index = 0
            if level > self.max_level or level > working_target:
                return False

