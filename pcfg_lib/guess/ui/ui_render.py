import time

from rich.box import ROUNDED, SIMPLE
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


#=======================================================================================================
#                                  TUIRenderer 클래스 정의
#=======================================================================================================
class TUIRenderer:
    #----------------------------------------------------------------------------------
    # 초기화 및 기본 속성 설정
    # hashes: 크랙 대상 해시 집합
    # config: 설정 딕셔너리 (mode 등)
    #----------------------------------------------------------------------------------
    def __init__(self, hashes: set[str], config: dict):
        self.hashes = hashes                        # 대상 해시 목록
        self.cfg = config                          # 설정 매개변수
        self.console = Console()                   # Rich 콘솔 객체

    #----------------------------------------------------------------------------------
    # 세션 초기 화면 렌더링
    # session: PCFGSession 인스턴스
    #----------------------------------------------------------------------------------
    def initial(self, session):
        self.session = session                     # 세션 참조 저장
        return self.layout(0)                     # 생성된 시도 수 0 으로 레이아웃 반환

    #----------------------------------------------------------------------------------
    # UI 업데이트용 렌더링
    # 세션에서 생성된 비밀번호 수를 사용해 레이아웃 재생성
    #----------------------------------------------------------------------------------
    def update(self):
        return self.layout(self.session.generated)

    #----------------------------------------------------------------------------------
    # 전체 레이아웃 구성
    # gen_count: 현재까지 생성된 비밀번호 수
    # Columns 및 텍스트 그룹으로 화면 구성
    #----------------------------------------------------------------------------------
    def layout(self, gen_count: int):
        return Group(
            Columns([
                self._make_table(gen_count),        # 좌측: 해시 상태 테이블
                self._make_panel()                  # 우측: 최근 시도 비밀번호 패널
            ], expand=True),
            Text("Press 'q' to quit", style="bold yellow", justify="center")
        )

    #=======================================================================================================
    #                               내부 렌더링 메소드
    #=======================================================================================================

    #----------------------------------------------------------------------------------
    # 상태 테이블 생성
    # gen_count: 생성된 비밀번호 수
    #----------------------------------------------------------------------------------
    def _make_table(self, gen_count: int) -> Table:
        if self.cfg["use_john"]:
            mode = "john the ripper"
        else:
            mode = self.cfg.get('mode', 'md5')
        # 테이블 기본 설정
        tbl = Table(
            title=f"PCFG Cracking (mode:{mode})",
            title_style="bold white on dark_blue",
            box=ROUNDED, border_style="bright_blue", header_style="bold cyan",
            expand=True, show_lines=True
        )
        # 컬럼 정의
        tbl.add_column("Hash", style="magenta", no_wrap=True)
        tbl.add_column("Status", style="yellow", justify="center")
        tbl.add_column("Plaintext", style="green")
        tbl.add_column("Elapsed", style="cyan")

        # 경과 시간 계산
        elapsed = int(time.time() - self.session.start_ts)

        # 각 해시에 대해 상태 및 결과 추가
        for h in self.hashes:
            if h in self.session.found:
                pw, t, gen0 = self.session.found[h]
                tbl.add_row(h, "[green]Cracked", pw, f"{t:.1f}s (on gen : {gen0} items)")
            else:
                tbl.add_row(h, "[red]Pending", "", "")

        # 테이블 하단 캡션 설정
        tbl.caption = (
            f"Finished: {len(self.session.found)}/{len(self.hashes)}  "
            f"Generated: {gen_count}  Elapsed: {elapsed}s"
        )
        return tbl

    #----------------------------------------------------------------------------------
    # 최근 시도 비밀번호 패널 생성
    # 최근 리스트 출력, 없으면 안내 메시지
    #----------------------------------------------------------------------------------
    def _make_panel(self) -> Panel:
        # 최근 생성된 비밀번호 문자열 생성
        body = "\n".join(self.session.recent) or "[dim]No guesses yet"
        return Panel(
            body,
            title=f"Recent (prob={self.session.current_prob:.3g})",
            box=SIMPLE,
            expand=False
        )
