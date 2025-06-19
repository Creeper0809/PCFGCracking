import hashlib
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from multiprocessing import Queue

from pcfg_lib.guess.pcfg.pcfg_guesser import PCFGGuesser, TreeItem


#=======================================================================================================
#                                WorkerManager 클래스 정의
#=======================================================================================================
class WorkerManager:
    #----------------------------------------------------------------------------------
    # 초기화 및 기본 속성 설정
    # config: 설정 딕셔너리 (코어 수, 해시 모드 등)
    # guess_q: 비밀번호 전달용 공유 큐
    # exit_evt: 종료 이벤트 플래그
    # targets: 크랙 대상 해시 목록 (Manager 공유)
    #----------------------------------------------------------------------------------
    def __init__(self, config, guess_q: Queue, exit_evt, targets):
        self.config = config                   # 전체 설정
        self.guess_q = guess_q                 # 전역 추측 큐
        self.exit_evt = exit_evt               # 종료 신호 이벤트
        self.targets = targets                 # 남은 해시 리스트/집합
        self.pool = None                       # ProcessPoolExecutor 인스턴스
        self.inflight = {}                     # {Future: TreeItem} 진행중인 작업 맵

    #=======================================================================================================
    #                          워커 풀 초기화 및 시작 메소드
    #=======================================================================================================
    def start(self):
        """ProcessPoolExecutor 시작 및 초기화"""
        self.pool = ProcessPoolExecutor(
            max_workers=self.config.get("core", 4),
            initializer=self._init_worker,
            initargs=(self.config, self.guess_q, self.exit_evt, self.targets)
        )

    @staticmethod
    def _init_worker(config, guess_q, exit_evt, targets):
        """워커 프로세스별 전역 환경 설정 (초기화 함수)"""
        global pcfg_worker, GUESS_QUEUE, EXIT_EVENT, TARGET_HASHES, HASH_MODE, BUFFER_SIZE
        pcfg_worker = PCFGGuesser(config=config)         # PCFGGuesser 인스턴스
        GUESS_QUEUE = guess_q                            # 전역 비밀번호 큐
        EXIT_EVENT = exit_evt                            # 전역 종료 이벤트
        TARGET_HASHES = targets                          # 전역 남은 해시 목록
        HASH_MODE = config.get("mode", "md5")         # 해시 알고리즘
        BUFFER_SIZE = config.get("buffer_size", 1000)  # 내부 버퍼 크기

    #=======================================================================================================
    #                                내부 유틸리티 메소드
    #=======================================================================================================
    @staticmethod
    def _compare_batch(batch):
        """버퍼 배치(batch)와 TARGET_HASHES 비교, 일치하는 항목 반환"""
        matches = []
        for pw in batch:
            d = getattr(hashlib, HASH_MODE)(pw.encode()).hexdigest()
            if d in TARGET_HASHES:
                TARGET_HASHES.remove(d)
                matches.append((d, pw))
        return matches

    @staticmethod
    def _process_node(node: TreeItem):
        """단일 TreeItem 노드 처리:
        1) PCFGGuesser로 비밀번호 생성
        2) GUESS_QUEUE 및 내부 버퍼에 추가
        3) BUFFER_SIZE마다 _compare_batch 실행
        4) 자식 노드 리스트 반환
        """
        if EXIT_EVENT.is_set():
            pcfg_worker.is_exit = True
            return [], []  # 종료 시 빈 결과 반환
        buf, out = [], []
        try:
            for pw in pcfg_worker.guess(node.structures):
                if EXIT_EVENT.is_set():
                    raise InterruptedError()
                GUESS_QUEUE.put(pw)
                buf.append(pw)
                if len(buf) >= BUFFER_SIZE:
                    out.extend(WorkerManager._compare_batch(buf))
                    buf.clear()
            children = pcfg_worker.find_children(node)
        except InterruptedError:
            children = []  # 인터럽트 시 자식 생성 생략
        finally:
            # 남은 버퍼 처리
            if buf:
                out.extend(WorkerManager._compare_batch(buf))
        return children, out

    #=======================================================================================================
    #                                작업 제출 및 결과 수집
    #=======================================================================================================
    def submit(self, node: TreeItem):
        """새로운 TreeItem 노드 워커 풀에 제출"""
        fut = self.pool.submit(self._process_node, node)
        self.inflight[fut] = node

    def collect(self, timeout=0.5):
        """완료된 Future 작업 수거 및 결과 반환
        timeout: 대기 시간(초)
        반환: [(children, matches), ...] 리스트
        """
        done, _ = wait(self.inflight, timeout=timeout, return_when=FIRST_COMPLETED)
        results = []
        for fut in done:
            node = self.inflight.pop(fut)
            children, matches = fut.result()
            results.append((children, matches))
        return results

    #=======================================================================================================
    #                                작업 취소 및 종료
    #=======================================================================================================
    def cancel_all(self):
        """모든 진행 중인 Future 취소"""
        for fut in list(self.inflight):
            fut.cancel()
        self.inflight.clear()

    def shutdown(self):
        """워커 풀 즉시 종료 (대기하지 않고)"""
        if self.pool:
            self.pool.shutdown(wait=False, cancel_futures=True)
