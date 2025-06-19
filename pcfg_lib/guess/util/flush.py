import abc
import hashlib
import shutil
import subprocess
import time
from pathlib import Path


#=======================================================================================================
#                             버퍼 관리 추상 기반 클래스 정의
#=======================================================================================================
class BufferManagerBase(abc.ABC):
    #----------------------------------------------------------------------------------
    # 초기화: 버퍼 크기 설정 및 내부 상태 초기화
    # buf_size: 플러시를 트리거할 최대 버퍼 크기
    #----------------------------------------------------------------------------------
    def __init__(self, buf_size: int):
        self.buf_size = buf_size       # 버퍼 크기 한계
        self._buffer  = []             # 비밀번호 임시 저장 리스트
        self._last    = time.time()    # 마지막 플러시 시각

    #----------------------------------------------------------------------------------
    # 버퍼에 비밀번호 추가
    # pw: 추가할 비밀번호 문자열
    #----------------------------------------------------------------------------------
    def add(self, pw: str):
        self._buffer.append(pw)

    #----------------------------------------------------------------------------------
    # 플러시 조건 확인: 버퍼가 가득 찼거나 시간이 경과했으면 True 반환
    #----------------------------------------------------------------------------------
    def should_flush(self):
        return (len(self._buffer) >= self.buf_size) or (time.time() - self._last > 3)

    #----------------------------------------------------------------------------------
    # 플러시 처리: 서브 클래스에서 구현해야 함
    # 반환: [(digest, pw), ...] 형태의 매칭 결과 리스트
    #----------------------------------------------------------------------------------
    @abc.abstractmethod
    def flush(self):
        pass


#=======================================================================================================
#                           메모리 기반 버퍼 관리 클래스
#=======================================================================================================
class MemoryBufferManager(BufferManagerBase):
    #----------------------------------------------------------------------------------
    # 초기화: 대상 해시 집합과 해시 모드 설정
    # buf_size: 버퍼 크기, targets: 검사용 해시 집합, HASH_MODE: 해시 알고리즘
    #----------------------------------------------------------------------------------
    def __init__(self, buf_size: int, targets: set[str], HASH_MODE="md5"):
        super().__init__(buf_size)
        self.targets = targets     # 남은 해시 집합
        self.HASH_MODE = HASH_MODE # 사용할 해시 알고리즘

    #----------------------------------------------------------------------------------
    # 플러시 처리: 버퍼에 있는 비밀번호로 해시를 생성하여 매칭 검사
    # 일치하는 해시는 targets에서 제거하고 결과로 반환
    #----------------------------------------------------------------------------------
    def flush(self):
        matches = []
        for pw in self._buffer:
            d = getattr(hashlib, self.HASH_MODE)(pw.encode()).hexdigest()
            if d in self.targets:
                self.targets.remove(d)
                matches.append((d, pw))
        self._buffer.clear()         # 버퍼 초기화
        self._last = time.time()     # 마지막 플러시 시간 업데이트
        return matches


#=======================================================================================================
#                          John-the-Ripper 연동 버퍼 관리 클래스
#=======================================================================================================
class JohnBufferManager(BufferManagerBase):
    #----------------------------------------------------------------------------------
    # 초기화: 해시 파일 경로와 세션명 설정
    # buf_size: 버퍼 크기, hashfile: 해시 파일 경로, session: JtR 세션 이름
    #----------------------------------------------------------------------------------
    def __init__(self, buf_size: int, hashfile: Path, session: str):
        super().__init__(buf_size)
        self.hashfile = hashfile     # 해시가 저장된 파일 경로
        self.session  = session      # John 세션 이름
        self.potfile  = Path(f"{session}.pot")  # pot 파일 경로
        self._offset  = 0            # 파일 읽기 오프셋

    #----------------------------------------------------------------------------------
    # 플러시 처리: stdin 입력으로 john 실행, pot 파일에서 새로운 크랙 결과 읽기
    # 반환: [(digest, pw), ...] 형태의 매칭 결과 리스트
    #----------------------------------------------------------------------------------
    def flush(self):
        if not self._buffer:
            return []

        # john 바이너리 경로 확인
        john = shutil.which("john") or shutil.which("john.exe")
        if not john:
            raise FileNotFoundError("john not in PATH")

        # stdin 모드로 john 실행
        cmd = [john, f"--session={self.session}", f"--pot={self.potfile}",
               "--stdin", str(self.hashfile)]
        subprocess.run(
            cmd,
            input="\n".join(self._buffer) + "\n",
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 버퍼 초기화 및 시간 갱신
        self._buffer.clear()
        self._last = time.time()

        # pot 파일에서 새로운 매칭 결과 파싱
        matches = []
        if self.potfile.exists():
            with self.potfile.open(encoding="utf-8", errors="ignore") as f:
                f.seek(self._offset)
                for ln in f:
                    if ':' in ln:
                        h, pw = ln.rstrip().split(':', 1)
                        matches.append((h, pw))
                self._offset = f.tell()
        return matches
