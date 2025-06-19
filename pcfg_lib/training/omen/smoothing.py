import math
from typing import Tuple


def smooth_grammar(grammar, ip_total, ep_total):
    # grammar: {prefix_str: index_obj}
    # ip_total: IP (initial prefix) 총 등장 횟수
    # ep_total: EP (ending prefix) 총 등장 횟수
    # 레벨 조정 계수 정의 (시작, 중간, 끝)
    level_adjust_factor = {
        'start': 250,
        'middle': 2,
        'end': 250,
    }
    for prefix, index in grammar.items():
        # 시작 부분에 대한 레벨 계산
        index.start_level = _calc_level(
            index.count_at_start,  # 이 prefix가 시작으로 사용된 횟수
            ip_total,
            level_adjust_factor['start']
        )

        # 끝 부분에 대한 레벨 계산
        index.end_level = _calc_level(
            index.count_at_end,    # 이 prefix가 끝으로 사용된 횟수
            ep_total,
            level_adjust_factor['end']
        )

        # 중간 부분(조건부 확률)에 대한 레벨 업데이트
        for next_char, cp_count in index.next_letter_candidates.items():
            # cp_count: (레벨, 횟수) 또는 횟수만 있던 경우
            # 레벨 재계산: 후보 문자의 횟수 대비 전체 중간 등장 횟수
            new_level = _calc_level(
                cp_count,                 # 조건부 확률로 등장한 횟수
                index.count_in_middle,    # 중간 위치에서의 총 등장 횟수
                level_adjust_factor['middle']
            )
            # next_letter_candidates에 (level, count) 튜플로 저장
            index.next_letter_candidates[next_char] = (new_level, cp_count)


def smooth_length(ln_lookup, ln_counter, max_level=10):
    # ln_lookup: 길이별 레벨 정보 리스트 (대개 (level, count) 저장)
    # ln_counter: 길이별 총 빈도 합
    for i, count in enumerate(ln_lookup):
        try:
            # 길이 i+1에 대한 레벨 계산: 등장 횟수 대비 전체 길이 빈도
            level = _calc_level(count, ln_counter, 1)
            ln_lookup[i] = (level, count)
        except ZeroDivisionError:
            # ln_counter가 0인 경우 기본 최대 레벨로 설정
            ln_lookup[i] = (max_level, 0)


def _calc_level(base_count: int, total_count: int, level_adjust_factor: float, max_level: int = 10) -> int:
    # base_count: 특정 이벤트(시작/중간/끝) 발생 횟수
    # total_count: 해당 이벤트 전체 발생 횟수
    # level_adjust_factor: 레벨 조정 계수
    # max_level: 허용할 최대 레벨

    # 발생 비율 계산 후 계수 적용
    prob_i = base_count / total_count
    prob_i *= level_adjust_factor
    prob_i += 1e-11   # 로그 계산 시 0 방지용 작은 값

    # -log 확률 값 바닥(소수점 이하 버림)
    level = math.floor(-math.log(prob_i))

    # 레벨 범위 보정 (0 <= level <= max_level)
    if level < 0:
        level = 0
    elif level > max_level:
        level = max_level

    return level
