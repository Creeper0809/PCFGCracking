# =====================
# Imports and Globals
# =====================
import sys
import time
import threading
import queue as std_queue
from collections import deque
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from multiprocessing import Queue, Manager, current_process

from readchar import readkey
from rich.live import Live
from rich.console import Console, Group
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, SIMPLE

from lib.guess.pcfg.pcfg_guesser import PCFGGuesser, TreeItem
from lib.guess.util.priority_queue import PcfgQueue

# 전역 변수 선언
pcfg_worker = None
GUESS_QUEUE = None
WORKER_STATUS = None
EXIT_EVENT = None
LIVE = None

# =====================
# Worker Initialization
# =====================
def _init_worker(config, guess_queue, status_dict, exit_event):
    # 워커 프로세스에서 사용될 PCFGGuesser, 공유 큐, 상태 딕셔너리, 종료 이벤트 설정
    global pcfg_worker, GUESS_QUEUE, WORKER_STATUS, EXIT_EVENT
    pcfg_worker = PCFGGuesser(config=config)
    GUESS_QUEUE = guess_queue
    WORKER_STATUS = status_dict
    EXIT_EVENT = exit_event

# =====================
# Input Handling
# =====================
def _keypress(pcfg, exit_event):
    # 사용자 키 입력을 비동기적으로 처리
    global LIVE
    while True:
        ch = readkey()
        if ch.lower() == 'q':
            print("Exiting...")
            exit_event.set()
            break
        elif ch.lower() == 'r':
            # Live 인스턴스가 있을 때 강제 리프레시
            if LIVE:
                LIVE.refresh()

# =====================
# Node Processing
# =====================
def _process_node(node: TreeItem):
    # 종료 이벤트가 설정되면 즉시 반환
    if EXIT_EVENT.is_set():
        return [], []
    # 기존 출력 함수 보관
    orig_print = pcfg_worker.print_guess

    def wrap_guess(guess: str):
        # 종료 이벤트 중간 확인 및 예외 발생
        if EXIT_EVENT.is_set():
            pcfg_worker.exit_now = True
            raise InterruptedError()
        # 새 추측을 큐에 추가하고 워커 상태 업데이트
        GUESS_QUEUE.put(guess)
        WORKER_STATUS[current_process().name] = pcfg_worker.made_password
        orig_print(guess)

    # 출력 래핑
    pcfg_worker.print_guess = wrap_guess
    try:
        # 실제 추측 수행
        pcfg_worker.guess(node.structures)
    except InterruptedError:
        children, matches = [], []
    else:
        # 자식 노드 및 매치 결과 조회
        children = pcfg_worker.find_children(node)
        matches = list(pcfg_worker.found.items())
    # 출력 함수 복원
    pcfg_worker.print_guess = orig_print
    return children, matches

# =====================
# UI and Main Loop
# =====================
class CrackSession:
    def __init__(self, config):
        # 메인 PCFGGuesser 인스턴스 설정
        self.pcfg = PCFGGuesser(config=config)
        self.config = config

    def start_parallel_guess(self):
        console = Console()
        hashes = list(self.pcfg.target_hashes)
        found = {}
        recent_guesses = deque(maxlen=10)
        start_ts = time.time()
        now_prob = 0.0

        # 프로세스간 통신용 매니저 객체 생성
        manager = Manager()
        guess_queue = Queue()
        status_dict = manager.dict()
        exit_event = manager.Event()

        # 키 입력 스레드 시작
        user_thread = threading.Thread(target=_keypress, args=(self.pcfg, exit_event))
        user_thread.daemon = True
        user_thread.start()

        # 테이블 생성 함수
        def make_main_table(in_progress):
            elapsed = int(time.time() - start_ts)
            tbl = Table(
                title=f"PCFG Cracking Status (mode:{self.config['mode']})",
                title_style="bold white on dark_blue",
                box=ROUNDED, border_style="bright_blue",
                header_style="bold cyan", expand=True,
                show_lines=True,pad_edge=True,
                show_edge=True,
            )
            # 컬럼 정의
            tbl.add_column("Hash", style="magenta", no_wrap=True)
            tbl.add_column("Status", style="yellow", justify="center")
            tbl.add_column("Plaintext", style="green")
            tbl.add_column("Elapsed", style="cyan")

            for h in hashes:
                if h in found:
                    status = "[green]Cracked"
                    plaintext = found[h][0]
                    elapsed_s = f"{found[h][1]:.2f}s"
                else:
                    status = "[red]Pending"
                    plaintext = ""
                    elapsed_s = ""
                tbl.add_row(h, status, plaintext, elapsed_s)

            tbl.caption = (
                f"Finished: {len(found)}/{len(hashes)}    "
                f"Generated: {in_progress}    Elapsed: {elapsed}s"
            )
            return tbl

        # 최근 추측 패널 함수
        def make_recent_panel():
            body = "\n".join(recent_guesses) or "[dim]No guesses yet"
            return Panel(
                body, title=f"Recent Guesses (prob: {now_prob:.3f})",
                box=SIMPLE, expand=False
            )

        # Live 화면 설정 (alternate buffer)
        with Live(console=console, refresh_per_second=1, screen=True) as live:
            global LIVE
            LIVE = live
            queue = PcfgQueue(pcfg=self.pcfg)

            # 초기 레이아웃
            layout = Group(
                Columns([make_main_table(0), make_recent_panel()], expand=True),
                Text("Press 'q' to exit or 'r' to refresh", style="bold yellow", justify="center")
            )
            live.update(layout)

            # 워커 풀 및 메인 루프
            with ProcessPoolExecutor(
                max_workers=self.config['core'],
                initializer=_init_worker,
                initargs=(self.config, guess_queue, status_dict, exit_event)
            ) as exe:
                in_flight = {}
                while not exit_event.is_set() and len(found) < len(hashes):
                    # 키 입력 폴링
                    if exit_event.is_set():
                        break
                    # 워커에 노드 제출
                    while len(in_flight) < self.config['core']:
                        node = queue.pop()
                        if not node:
                            break
                        now_prob = node.prob
                        fut = exe.submit(_process_node, node)
                        in_flight[fut] = node
                    # 완료된 태스크 처리 또는 1초 후 리턴
                    done, _ = wait(in_flight, timeout=1, return_when=FIRST_COMPLETED)
                    for fut in done:
                        in_flight.pop(fut)
                        children, matches = fut.result()
                        for dg, pw in matches:
                            if dg not in found:
                                found[dg] = (pw, time.time() - start_ts)
                        for c in children:
                            queue.push(c)
                    # 큐에서 새로운 guess 수집
                    try:
                        while True:
                            recent_guesses.append(guess_queue.get_nowait())
                    except std_queue.Empty:
                        pass
                    # 진행 현황 업데이트
                    in_progress = sum(status_dict.values())
                    layout = Group(
                        Columns([make_main_table(in_progress), make_recent_panel()], expand=True),
                        Text("Press 'q' to exit or 'r' to refresh", style="bold yellow", justify="center")
                    )
                    live.update(layout)

        # 종료 후 최종 화면 출력
        end_ts = time.time()
        layout = Group(
            Columns([make_main_table(in_progress), make_recent_panel()], expand=True),
            Text("Press 'q' to exit or 'r' to refresh", style="bold yellow", justify="center")
        )
        console.print(layout)
        console.print(f"[bold green]Finished[/] — cracked {len(found)}/{len(hashes)} hashes in {end_ts - start_ts:.2f}s")