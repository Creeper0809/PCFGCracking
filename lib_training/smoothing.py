import math

def smooth_grammar(grammar, ip_total, ep_total):
    # 스무딩에 사용할 level 조정 계수를 설정합니다.
    # 추후 설정 옵션으로 옮길 수 있습니다.
    level_adjust_factor = {
        'start': 250,
        'middle': 2,
        'end': 250,
    }

    # (ngram-1) 길이의 접두 문자열 목록을 순회하며,
    # IP·EP 카운트와 다음 글자 전이 정보를 처리합니다.
    for starting_letters in grammar.keys():
        # 딕셔너리 참조를 변수에 할당해 코드를 간결하게 합니다.
        index = grammar[starting_letters]

        # 시작 위치(initial position) 스무딩 레벨 계산 및 저장
        index.start_level = _calc_level(
            index.count_at_start, ip_total, level_adjust_factor['start']
        )

        # 종료 위치(end position) 스무딩 레벨 계산 및 저장
        index.end_level = _calc_level(
            index.count_at_end, ep_total, level_adjust_factor['end']
        )

        # 모든 조건부 확률(next_letter 전이)을 순회합니다.
        for cond_prob in index.next_letter_candidates:
            cp_count = index.next_letter_candidates[cond_prob]
            # 전이 스무딩 레벨 계산
            level = _calc_level(
                cp_count, index.count_in_middle, level_adjust_factor['middle']
            )
            # (level, 원본 count) 튜플로 저장
            index.next_letter_candidates[cond_prob] = (level, cp_count)


def smooth_length(ln_lookup, ln_counter, max_level=10):
    # 길이별 항목을 순회하며 스무딩 레벨을 계산합니다.
    for length, count in enumerate(ln_lookup):
        try:
            # 스무딩 레벨 계산
            level = _calc_level(count, ln_counter, 1)
            ln_lookup[length] = (level, count)
        except ZeroDivisionError:
            # ln_counter == 0인 경우 level을 최대 레벨로 설정
            ln_lookup[length] = (max_level, 0)


def _calc_level(base_count, total_count, level_adjust_factor, max_level=10):
    # 확률(probi) 계산: base_count/total_count * 조정계수 + 오프셋
    probi = base_count / total_count
    probi *= level_adjust_factor
    probi += 1e-11  # underflow 방지

    # level = floor(-log(probi))
    level = math.floor(-math.log(probi))

    # level이 [0, max_level] 범위 안에 있도록 보정
    if level < 0:
        level = 0
    elif level > max_level:
        level = max_level

    return level
