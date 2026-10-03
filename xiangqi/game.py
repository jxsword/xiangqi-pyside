"""game.py — 对局状态控制器（纯逻辑，不依赖 Qt，便于单元测试）。

支持双人对战、人机对战（人执红、AI 执黑）、悔棋、胜负判定。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .board import BLACK, RED, Board, DISPLAY, Move, Piece
from .engine import Engine

PVP = "pvp"          # 双人对战
PVE = "pve"          # 人机对战（人执红）


@dataclass
class HistoryEntry:
    move: Move
    captured: Piece


class GameState:
    def __init__(self, mode: str = PVP, ai_depth: int = 3) -> None:
        self.board = Board()
        self.engine = Engine()
        self.mode = mode
        self.ai_depth = ai_depth
        self.selected: Optional[Tuple[int, int]] = None
        self.legal_targets: List[Move] = []
        self.history: List[HistoryEntry] = []
        self.game_over = False
        self.winner: Optional[int] = None  # RED/BLACK/None
        self.ai_thinking = False

    # ---------- 状态文本 ----------
    def status_text(self) -> str:
        if self.game_over:
            side = "红方" if self.winner == RED else "黑方"
            return f"{side}胜！"
        if self.ai_thinking:
            return "AI（黑方）思考中…"
        turn = "红方走棋" if self.board.is_red_turn() else "黑方走棋"
        color = RED if self.board.is_red_turn() else BLACK
        check = "（将军！）" if self.board.is_in_check(color) else ""
        return turn + check

    def mode_name(self) -> str:
        return "人机对战（黑方为 AI）" if self.mode == PVE else "双人对战"

    def display_at(self, r: int, c: int) -> str:
        p = self.board.piece_at(r, c)
        return "" if p.empty() else DISPLAY[(p.type, p.color)]

    def piece_color_at(self, r: int, c: int) -> Optional[int]:
        p = self.board.piece_at(r, c)
        return None if p.empty() else p.color

    def is_legal_target(self, r: int, c: int) -> bool:
        return any(m.tr == r and m.tc == c for m in self.legal_targets)

    # ---------- 流程 ----------
    def new_game(self, mode: Optional[str] = None) -> None:
        if mode is not None:
            self.mode = mode
        self.board.reset()
        self.selected = None
        self.legal_targets = []
        self.history.clear()
        self.game_over = False
        self.winner = None
        self.ai_thinking = False

    def _current_color(self) -> int:
        return RED if self.board.is_red_turn() else BLACK

    def _record_move(self, m: Move) -> bool:
        color = self._current_color()
        captured = self.board.make_move(m, color)
        if captured is None:
            return False
        self.history.append(HistoryEntry(m, captured))
        self._after_move()
        return True

    def _after_move(self) -> None:
        next_color = self._current_color()
        if self.board.has_no_legal_moves(next_color):
            self.game_over = True
            self.winner = RED if next_color == BLACK else BLACK

    def click(self, r: int, c: int) -> bool:
        """玩家点击棋盘。返回状态是否发生变化（供 UI 刷新）。"""
        if self.game_over or self.ai_thinking:
            return False
        color = self._current_color()
        # 人机模式下，黑方回合不接受玩家输入
        if self.mode == PVE and color == BLACK:
            return False

        # 已选中且点击合法目标 → 走子
        if self.selected is not None and self.is_legal_target(r, c):
            m = next(m for m in self.legal_targets if m.tr == r and m.tc == c)
            ok = self._record_move(m)
            self.selected = None
            self.legal_targets = []
            return ok

        piece = self.board.piece_at(r, c)
        if not piece.empty() and piece.color == color:
            self.selected = (r, c)
            self.legal_targets = [
                m for m in self.board.generate_moves(color)
                if m.fr == r and m.fc == c
            ]
            return True
        self.selected = None
        self.legal_targets = []
        return True

    def ai_move(self) -> bool:
        """AI（黑方）走一步。返回是否走子。"""
        if self.game_over or self.mode != PVE or self.board.is_red_turn():
            return False
        self.ai_thinking = True
        try:
            m = self.engine.best_move(self.board, BLACK, self.ai_depth)
            if m is None:
                self.game_over = True
                self.winner = RED
                return False
            self._record_move(m)
            return True
        finally:
            self.ai_thinking = False

    def undo(self) -> bool:
        """悔棋：双人撤 1 步；人机撤到玩家上一步之前（撤 2 步，不足则尽撤）。"""
        if self.ai_thinking:
            return False
        steps = 2 if self.mode == PVE else 1
        steps = min(steps, len(self.history))
        if steps == 0:
            return False
        for _ in range(steps):
            entry = self.history.pop()
            self.board.undo_move(entry.move, entry.captured)
        self.game_over = False
        self.winner = None
        self.selected = None
        self.legal_targets = []
        return True
