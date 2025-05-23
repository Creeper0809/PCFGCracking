import math
import time
import hashlib
import multiprocessing
from collections import deque
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.box import ROUNDED, SIMPLE

from guess.pcfg_guesser import PCFGGuesser, TreeItem
from guess.priority_queue import PcfgQueue

pcfg_worker = None


def init_worker(config):
    global pcfg_worker
    pcfg_worker = PCFGGuesser(config=config)


def process_node(node: TreeItem):
    before = len(pcfg_worker.recent_guesses)

    node_guesses = []

    orig_print = pcfg_worker.print_guess

    def wrap_guess(guess: str):
        orig_print(guess)
        node_guesses.append(guess)

    pcfg_worker.print_guess = wrap_guess

    cnt = pcfg_worker.guess(node.structures)
    children = pcfg_worker.find_children(node)

    pcfg_worker.print_guess = orig_print

    new_last10 = node_guesses[-10:]
    matches = list(pcfg_worker.found.items())
    return cnt, children, matches, new_last10


class CrackSession:
    def __init__(self, config):
        self.pcfg = PCFGGuesser(config=config)

    def start_parallel_guess(self, config):
        console = Console()
        hashes = list(self.pcfg.target_hashes)
        found = {}
        total_count = 0
        start_ts = time.time()
        recent_guesses = deque(maxlen=10)

        def make_main_table():
            elapsed = int(time.time() - start_ts)
            tbl = Table(
                title=" PCFG Cracking Status ",
                title_style="bold white on dark_blue",
                box=ROUNDED,
                border_style="bright_blue",
                header_style="bold cyan",
                show_lines=True,
                pad_edge=True,
                show_edge=True,
                expand=True
            )
            tbl.add_column("Hash", style="magenta", no_wrap=True)
            tbl.add_column("Status", style="yellow", justify="center")
            tbl.add_column("Plaintext", style="green")
            for h in hashes:
                if h in found:
                    tbl.add_row(h, "[bold green]Cracked", found[h])
                else:
                    tbl.add_row(h, "[red]Pending", "")
            tbl.caption = f"Generated: {total_count}    Elapsed: {elapsed}s"
            return tbl

        def make_recent_panel():
            body = "\n".join(recent_guesses) or "[dim]No guesses yet"
            return Panel(
                body,
                title=" Recent Guesses ",
                title_align="left",
                border_style="bright_blue",
                box=SIMPLE,
                padding=(1, 2),
                expand=False,
            )

        with Live(console=console, refresh_per_second=1) as live:
            queue = PcfgQueue(pcfg=self.pcfg)
            live.update(Columns([make_main_table(), make_recent_panel()], expand=True))

            with ProcessPoolExecutor(
                    max_workers=config["core"],
                    initializer=init_worker,
                    initargs=(config,)
            ) as exe:
                in_flight = {}
                while True:

                    if len(found) == len(hashes):
                        break

                    while len(in_flight) < config["core"]:
                        node = queue.pop()
                        if not node:
                            break
                        fut = exe.submit(process_node, node)
                        in_flight[fut] = node

                    if not in_flight:
                        break

                    done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
                    for fut in done:
                        in_flight.pop(fut)
                        cnt, children, matches, last10 = fut.result()

                        total_count += cnt
                        for dg, pw in matches:
                            if dg not in found:
                                found[dg] = pw
                        for pwd in last10:
                            recent_guesses.append(pwd)
                        for c in children:
                            queue.push(c)

                    live.update(
                        Columns([make_main_table(), make_recent_panel()], expand=True)
                    )

        end_ts = time.time()
        console.print(
            f"[bold green]Finished[/] — tried {total_count} passwords in {end_ts - start_ts:.2f}s"
        )
        console.print(f"[bold]{len(found)}/{len(hashes)} cracked[/]")

    def start_guess(self, config=None):
        pcfg = PCFGGuesser(config=config)
        queue = PcfgQueue(pcfg=pcfg)
        password_count = 0

        print("\n\nstart guessing...")
        print("-" * 40)
        start = time.time()

        while True:
            next_node = queue.next()
            if next_node is None:
                break
            print(f"current structure : {''.join(s.symbol for s in next_node.structures)}")
            print(f"prob : {math.exp(next_node.prob) * 100:.6f}%")
            print("passwords : ")
            count = pcfg.guess(next_node.structures)
            password_count += count
            print(f"made password count : {count}")
            print(f"total password count : {password_count}")
            print("-" * 40)

        end = time.time()
        print("end guessing...")
        print(f"time taken : {end - start} sec")
