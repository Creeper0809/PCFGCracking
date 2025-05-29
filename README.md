# PCFGCracking

## 개요
PCFGCracking은 한국어 사용자 맞춤형 PCFG(Probabilistic Context-Free Grammar) 기반 비밀번호 크래킹 도구입니다.  
훈련(training)과 크래킹(cracking) 두 단계를 통해, 해시 파일(.hash)에 담긴 해시들을 빠르게 평문 비밀번호로 복원합니다.

## 주요 기능
- **PCFG 공격**: 한국어·영어 패턴에 최적화된 PCFG 기반 비밀번호 추측  
- **마르코프 공격**: Markov 체인 기반 비밀번호 추측 (옵션)  
- **병렬 처리**: `--core` 옵션으로 다중 프로세스 워커 실행  
- **사용자 정의 비밀번호 길이**: `--pw-min` / `--pw-max` 로 추측 길이 범위 지정  
- **로그 모드**: `-l/--log` 옵션으로 중간 단계 로깅 활성화  

## 요구 사항
- Python 3.8 이상
- 주요 파이썬 패키지:  
  ```
  jamo
  korean-romanizer
  eunjeon
  YaleKorean
  wordfreq
  rich
  readchar
  ```
- (선택) `Mecab` C 라이브러리: eunjeon 설치 시 필요

## 설치 방법
```bash
git clone https://github.com/yourname/PCFGCracking.git
cd PCFGCracking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 사용법

### 1. 모델 학습 (Training)
```bash
./password_train.py <데이터 파일(.db 또는 .txt)>
```
- 학습 설정: `config.ini`의 `[program_info]` 섹션 참조  
- 데이터 예시: `Resource/TrainingData/korean_password_candidates.txt`

### 2. 해시 크래킹 (Cracking)
```bash
./password_guess.py [OPTIONS] <candidate.hash>
```
**주요 옵션**  
- `-m, --mode`: 해시 알고리즘 (현재 `md5` 지원)  
- `-a, --attack-mode`: 0=PCFG only, 1=Markov only, 2=Both  
- `--pw-min`: 최소 비밀번호 길이  
- `--pw-max`: 최대 비밀번호 길이  
- `-c, --core`: 워커 수 (병렬 프로세스 개수)  
- `-l, --log`: 로깅 활성화  

`q` 키: 즉시 종료, `r` 키: 화면 갱신  

## 프로젝트 구조
```
PCFGCracking/
├── password_guess.py       # 크래킹 실행 스크립트
├── password_train.py       # 학습 실행 스크립트
├── config.ini              # 학습 설정 파일
├── candidate.hash          # 예시 해시 파일
├── sqlite3.db              # 내부 DB (학습/크래킹용)
├── Resource/               # 리소스 및 샘플 데이터
│   └── TrainingData/
│       ├── korean_password_candidates.txt
│       └── test.txt
└── lib/                    # 핵심 라이브러리 코드
    ├── data/               # 정제된 데이터 및 사전 파일
    │   ├── STOPWORD.txt
    │   └── korean_dict.db
    ├── guess/              # 크래킹(Guess) 모듈
    │   ├── omen/           # OMEN 알고리즘 기반 추측기
    │   │   ├── guess_structure.py
    │   │   ├── markov_guesser.py
    │   │   └── omen_io.py
    │   ├── pcfg/           # PCFG 기반 추측기
    │   │   ├── pcfg_guesser.py
    │   │   └── pcfg_io.py
    │   ├── util/           # 추측 우선순위 큐 등 내부 유틸
    │   │   └── priority_queue.py
    │   └── crack.py        # CrackSession 관리
    ├── training/           # 학습(Training) 모듈
    │   ├── detectors/      # 패턴 검출기(알파벳, 숫자, 자모 등)
    │   │   ├── alphabet_detection.py
    │   │   ├── digit_detection.py
    │   │   ├── keyboard_walk_detection.py
    │   │   ├── leet_detection.py
    │   │   ├── other_detection.py
    │   │   └── word_detection.py
    │   ├── io/             # 학습 데이터 파서 및 결과 출력
    │   │   ├── train_data_parser.py
    │   │   ├── pcfg_output.py
    │   │   └── omen_train_data_output.py
    │   ├── korean_dict/     # 한국어 사전 데이터 파싱 및 저장
    │   │   ├── data_parser/
    │   │   │   ├── BaseParser.py
    │   │   │   ├── korean_copus_parser.py
    │   │   │   └── word_parser.py
    │   │   └── io/          # 사전 입출력(parse_loanword, save_load)
    │   ├── util/           # 데이터 전처리 및 학습 도우미
    │   │   ├── korean.py
    │   │   └── english.py
    │   ├── omen/           # OMEN 학습 보조
    │   │   ├── evaluate_password.py
    │   │   └── omen_parser.py
    │   └── pcfg/           # PCFG 학습 보조
    │       ├── pcfg_parser.py
    │       └── word_trie.py
    ├── util/                # 전역 유틸리티(경로 설정 등)
    │   └── paths.py
    └── __init__.py
```
