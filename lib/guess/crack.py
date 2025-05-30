import threading
import time
from collections import deque
from multiprocessing import Manager, Queue
from pathlib import Path
from queue import Empty as QueueEmpty

from readchar import readkey
from rich.live import Live

from lib.guess.util.flush import MemoryBufferManager, JohnBufferManager
from lib.guess.pcfg.pcfg_guesser import PCFGGuesser
from lib.guess.ui.ui_render import TUIRenderer
from lib.guess.util.priority_queue import PcfgQueue
from lib.guess.util.worker_manage import WorkerManager


#=======================================================================================================
#                                PCFG 세션 관리 클래스 정의
#=======================================================================================================
class PCFGSession:
    #----------------------------------------------------------------------------------
    # 초기화 및 상태 변수 설정
    # config: 설정 딕셔너리 (hashfile 경로, session 이름, 코어 수 등)
    #----------------------------------------------------------------------------------
    def __init__(self, config: dict):
        self.cfg = config
        self.hashfile = Path(config.get("hashfile", ""))
        self.session = config.get("session", "pcfg_mem")
        self.start_ts = time.time()
        self.hashes = self._load_hashes()

        # 추적할 결과 및 통계
        self.found = {}                             # 찾은 해시 → (비밀번호, 걸린 시간, 시도 수)
        self.recent = deque(maxlen=10)              # 최근 생성된 비밀번호 히스토리
        self.generated = 0                          # 총 생성된 비밀번호 수
        self.current_prob = 0.0                     # 현재 확률 상태

        # 동기화 및 큐
        mgr = Manager()
        self.guess_q = Queue()                      # 워커에서 생성된 비밀번호 수집용 큐
        self.exit_evt = mgr.Event()                 # 종료 신호 이벤트
        self.targets = set(self.hashes)             # 남은 타겟 해시 집합

        # 구성요소 초기화
        self.worker = WorkerManager(config, self.guess_q, self.exit_evt, self.targets)
        self.buffer = MemoryBufferManager(
            config.get("buffer_size", 1000), self.targets, config.get("mode", "md5")
        )
        self.ui = TUIRenderer(self.hashes, config)

        # 키 입력 쓰레드 (q 입력 시 종료)
        threading.Thread(target=self._keypress, daemon=True).start()

    #----------------------------------------------------------------------------------
    # 해시 파일 로드: 파일이 존재하면 각 줄의 해시를 집합으로 반환
    #----------------------------------------------------------------------------------
    def _load_hashes(self):
        if not self.hashfile.is_file():
            return set()
        return {ln.strip() for ln in self.hashfile.open(encoding="utf-8") if ln.strip()}

    #----------------------------------------------------------------------------------
    # 키 입력 처리: 'q' 입력 시 종료 이벤트 설정
    #----------------------------------------------------------------------------------
    def _keypress(self):
        while True:
            if readkey().lower() == 'q':
                self.exit_evt.set()
                break

    #----------------------------------------------------------------------------------
    # 세션 실행: 워커 시작, 노드 제출, 결과 수집, TUI 업데이트, 종료 처리
    #----------------------------------------------------------------------------------
    def run(self):
        console = self.ui.console
        self.worker.start()

        # Live 화면 모드
        with Live(self.ui.initial(self), console=console, refresh_per_second=1, screen=True) as live:
            queue = PcfgQueue(pcfg=PCFGGuesser(config=self.cfg))

            while not self.exit_evt.is_set():
                # 1) 모든 해시를 찾았으면 종료
                if len(self.found) >= len(self.hashes):
                    self.exit_evt.set()
                    self.worker.cancel_all()
                    self.worker.shutdown()
                    break

                # 2) 워커에 처리할 노드 제출 (코어 수 제한)
                while len(self.worker.inflight) < self.cfg.get("core", 4):
                    nd = queue.pop()
                    if not nd:
                        break
                    self.current_prob = nd.prob
                    self.worker.submit(nd)

                # 3) 워커로부터 결과 수집 (자식 노드, 매칭된 비밀번호)
                for children, matches in self.worker.collect():
                    # 3-1) 매칭된 해시 처리
                    for d, pw in matches:
                        if d not in self.found:
                            self.found[d] = (pw, time.time() - self.start_ts, self.generated)
                    # 3-2) 새 노드 큐에 추가
                    for c in children:
                        queue.push(c)

                # 4) guess_q 에서 생성 비밀번호 꺼내 recent 및 버퍼에 추가
                try:
                    while True:
                        pw = self.guess_q.get_nowait()
                        self.recent.append(pw)
                        self.buffer.add(pw)
                        self.generated += 1
                except QueueEmpty:
                    pass

                # 5) 버퍼 플러시 시 실제 found 처리
                if self.buffer.should_flush():
                    for d, pw in self.buffer.flush():
                        if d not in self.found:
                            self.found[d] = (pw, time.time() - self.start_ts, self.generated)

                # 6) UI 업데이트
                live.update(self.ui.update())

        # 종료 후 최종 레이아웃 및 결과 출력
        console.print(self.ui.layout(self.generated))
        console.print(
            f"[bold green]Done![/] {len(self.found)}/{len(self.hashes)} cracked in {time.time() - self.start_ts:.1f}s generated {self.generated}"
        )


#=======================================================================================================
#                           John 모드 확장: PCFGSession 상속 클래스
#=======================================================================================================
class PCFGJohnSession(PCFGSession):
    #----------------------------------------------------------------------------------
    # JohnBufferManager 사용하도록 버퍼 및 targets 재설정
    #----------------------------------------------------------------------------------
    def __init__(self, config: dict):
        super().__init__(config)
        mgr = Manager()
        self.targets = mgr.list(self.hashes)
        self.buffer = JohnBufferManager(
            config.get("buffer_size", 1000),
            self.hashfile,
            self.session
        )
