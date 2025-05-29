from collections import Counter

def find_omen_level(omen_trainer, password):
    # 비밀번호 길이를 구함
    pw_len = len(password)
    # 허용 길이 범위를 벗어나면 -1 반환
    if pw_len < omen_trainer.min_length or pw_len > omen_trainer.max_length:
        return -1
    ngram = omen_trainer.ngram
    try:
        # 길이 기반 레벨 조회 (ln_lookup은 길이별 레벨 리스트)
        ln_level = omen_trainer.ln_lookup[pw_len - 1][0]

        # 초기 IP(시작 ngram-1자)에서 시작 레벨 획득
        chunk = password[0:ngram - 1]
        chain_level = omen_trainer.grammar[chunk].start_level

        end_pos = ngram
        # 이후 ngram 단위로 다음 문자 레벨을 더해가며 합산
        while end_pos <= pw_len:
            chunk = password[end_pos - ngram:end_pos]
            # 이전 문자열 key로 next_letter_candidates에서 레벨 획득
            chain_level += omen_trainer.grammar[chunk[:-1]].next_letter_candidates[chunk[-1]][0]
            end_pos += 1

        # 길이 레벨과 체인 레벨 합산하여 반환
        return ln_level + chain_level

    except KeyError:
        # 중간에 사전에 키가 없으면 -1 반환
        return -1


def _rec_calc_keyspace(omen_trainer, level, length, ip):
    # 캐시 초기화: length, ip 조합이 없으면 새로 생성
    if length not in omen_trainer.grammar[ip].keyspace_cache:
        omen_trainer.grammar[ip].keyspace_cache[length] = {}

    if level in omen_trainer.grammar[ip].keyspace_cache[length]:
        # 캐시된 결과 반환
        return omen_trainer.grammar[ip].keyspace_cache[length][level]

    # 초깃값 설정
    omen_trainer.grammar[ip].keyspace_cache[length][level] = 0

    if length == 1:
        # 남은 길이가 1일 경우, 다음 문자 후보 중 레벨이 정확히 일치하는 개수를 셈
        for last_letter, letter_level in omen_trainer.grammar[ip].next_letter_candidates.items():
            if letter_level[0] == level:
                omen_trainer.grammar[ip].keyspace_cache[length][level] += 1
    else:
        # 길이가 1보다 크면 재귀적으로 다음 상태의 키스페이스 계산
        for last_letter, letter_level in omen_trainer.grammar[ip].next_letter_candidates.items():
            if letter_level[0] <= level:
                # 다음 ip는 마지막 글자를 붙여 시프트
                next_ip = ip[1:] + last_letter
                # 남은 레벨과 길이를 줄여가며 재귀 호출
                omen_trainer.grammar[ip].keyspace_cache[length][level] += _rec_calc_keyspace(
                    omen_trainer,
                    level - letter_level[0],
                    length - 1,
                    next_ip
                )
    # 계산된 값 캐시에 저장 후 반환
    return omen_trainer.grammar[ip].keyspace_cache[length][level]


def calc_omen_keyspace(omen_trainer, max_level=20, max_keyspace=10_000_000_000):
    # 레벨별 전체 키스페이스를 저장하는 Counter
    keyspace = Counter()

    # 1부터 max_level까지 반복
    for level in range(1, max_level + 1):
        # 각 IP(시작 ngram-1 문자열)에 대해 처리
        for ip, ip_info in omen_trainer.grammar.items():
            # 길이 기반 레벨 차이 계산
            level_minus_ip = level - ip_info.start_level

            if level_minus_ip > 0:
                # 각 가능 길이(length)마다 LN(level lookup) 레벨 확인
                for idx, length_info in enumerate(omen_trainer.ln_lookup):
                    length = idx + 1
                    # ngram 이하 길이는 건너뜀
                    if length <= omen_trainer.ngram:
                        continue
                    # 길이 레벨이 남은 레벨 이하일 때
                    if length_info[0] <= level_minus_ip:
                        # 남은 레벨과 길이를 인자에 맞춰 rec 호출
                        keyspace[level] += _rec_calc_keyspace(
                            omen_trainer,
                            level_minus_ip - length_info[0],
                            length - omen_trainer.ngram + 1,
                            ip
                        )
                        # max_keyspace 초과 시 조기 종료
                        if keyspace[level] > max_keyspace:
                            return keyspace
        # 각 레벨 결과 출력 (디버그용)
        print(f"OMEN Keyspace for Level {level}: {keyspace[level]}")

    return keyspace
