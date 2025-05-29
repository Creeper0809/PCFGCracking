class GuessStructure:
    def __init__(self, cp, max_level, ip, cp_length, target_level, memorizer):
        # 첫 번째 추측인지 여부를 나타냅니다.
        self.first_guess = True

        # 조건부 확률 사전: {이전 문자열: {level: [가능한 다음 문자들]}}
        self.cp = cp

        # 최대 레벨 (target_level의 상한)
        self.max_level = max_level

        # 시작 IP 문자열 (초기 접두사)
        self.ip = ip

        # IP 길이 계산
        self.ip_length = len(self.ip)

        # IP 다음에 붙일 CP(조건부 확률) 개수
        self.cp_length = cp_length

        # 목표 레벨: 최종 추측 구조의 레벨 합
        self.target_level = target_level

        # 파싱 트리: [[이전 문자열, level, index], ...]
        self.parse_tree = []

        # 탐색 가속을 위한 optimizer 객체
        self.memorizer = memorizer

    def next_guess(self):
        """
        다음 추측 문자열을 반환합니다.
        더 이상 생성할 구조가 없으면 None을 반환합니다.
        """
        # 첫 추측 처리: parse_tree가 비어 있으면 초기 트리를 생성
        if not self.parse_tree:
            self.parse_tree = self._fill_out_parse_tree(self.ip, self.cp_length, self.target_level)
            if not self.parse_tree:
                return None
            return self._format_guess()

        # 트리의 마지막 요소를 가져와 인덱스 증가 시도
        last_item = self.parse_tree[-1]
        prev_str, level, idx = last_item
        # 같은 레벨의 다음 문자 인덱스를 사용할 수 있으면
        if idx + 1 < len(self.cp[prev_str][level]):
            last_item[2] += 1
            return self._format_guess()

        # 더 이상 증가할 수 없으면 트리에서 제거하고 위층으로 백트래킹
        element = self.parse_tree.pop()
        if not self.parse_tree:
            return None

        # 백트래킹 후에 남은 레벨 및 길이 계산
        req_length = 1
        req_level = element[1] + self.parse_tree[-1][1]

        # 트리가 빌 때까지 백트래킹하며 가능한 구조를 탐색
        while self.parse_tree:
            last_item = self.parse_tree[-1]
            last_item[2] += 1  # 인덱스 증가
            depth_level = last_item[1]

            # 같은 레벨에서 가능한 모든 문자 시도
            while last_item[2] < len(self.cp[last_item[0]][depth_level]):
                new_ip = element[0][:-1] + self.cp[last_item[0]][depth_level][last_item[2]]
                new_elements = self._fill_out_parse_tree(new_ip, req_length, req_level - depth_level)
                if new_elements is not None:
                    # 유효한 구조 발견 시 parse_tree에 추가 후 포맷
                    self.parse_tree += new_elements
                    return self._format_guess()
                last_item[2] += 1

            # 더 낮은 레벨로 이동하여 다시 시도
            if depth_level == 0:
                break
            cp_index, new_level = self._find_cp(last_item[0], depth_level - 1, 0)
            if cp_index is None:
                break
            last_item[1] = new_level
            last_item[2] = 0

            element = self.parse_tree.pop()
            req_length += 1
            if self.parse_tree:
                req_level += self.parse_tree[-1][1]

        return None

    def _format_guess(self):
        """
        현재 parse_tree를 기반으로 문자열을 조합하여 반환합니다.
        """
        guess = self.ip
        for prev_str, level, idx in self.parse_tree:
            guess += self.cp[prev_str][level][idx]
        return guess

    def _fill_out_parse_tree(self, ip, length, target_level):
        """
        주어진 ip, 남은 cp 길이, 목표 레벨로 parse_tree 구조를 생성합니다.
        실패 시 None 반환
        """
        # 남은 길이가 1인 경우 바로 find_cp로 찾기
        if length == 1:
            cp_indices, cp_level = self._find_cp(ip, target_level, target_level)
            if cp_indices is None:
                return None
            return [[ip, cp_level, 0]]

        # optimizer 캐시에 결과가 있는지 확인
        if length <= self.memorizer.max_length:
            found, result = self.memorizer.lookup(ip, length, target_level)
            if found:
                return result

        cur_level = target_level
        opt_target = target_level

        # 레벨을 0까지 감소시키며 가능한 cp 구조 찾기
        while cur_level >= 0:
            cp_indices, cp_level = self._find_cp(ip, cur_level, 0)
            if cp_indices is None:
                if length <= self.memorizer.max_length:
                    self.memorizer.update(ip, length, opt_target, None)
                return None

            for idx, seg in enumerate(cp_indices):
                next_ip = ip[1:] + seg
                subtree = self._fill_out_parse_tree(next_ip, length - 1, target_level - cp_level)
                if subtree is not None:
                    result = [[ip, cp_level, idx]] + subtree
                    if length <= self.memorizer.max_length:
                        self.memorizer.update(ip, length, opt_target, result)
                    return result

            cur_level = cp_level - 1

        if length <= self.memorizer.max_length:
            self.memorizer.update(ip, length, opt_target, None)
        return None

    def _find_cp(self, ip, top_level, bottom_level):
        """
        ip 문자열에 대해 top_level에서 bottom_level까지 가능한 CP 리스트와 레벨 반환
        실패 시 (None, None)
        """
        if ip not in self.cp:
            return None, None
        if self.max_level < top_level:
            top_level = self.max_level
        while top_level >= bottom_level:
            if top_level in self.cp[ip]:
                return self.cp[ip][top_level], top_level
            top_level -= 1
        return None, None
