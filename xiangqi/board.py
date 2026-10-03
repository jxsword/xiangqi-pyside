"""board.py — 中国象棋棋盘与规则引擎（PySide6 版，与 C++/QML 版规则同源）。

坐标约定：row 0 为黑方底线（棋盘上方），row 9 为红方底线（下方）；
col 0..8 为从左到右 9 列。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

ROWS = 10
COLS = 9

# 棋子类型
NONE, KING, ADVISOR, ELEPHANT, HORSE, ROOK, CANNON, SOLDIER = range(8)
# 颜色
RED, BLACK = 0, 1

# 显示字符（红方简体、黑方传统字形）
DISPLAY = {
    (KING, RED): "帅", (ADVISOR, RED): "仕", (ELEPHANT, RED): "相",
    (HORSE, RED): "马", (ROOK, RED): "车", (CANNON, RED): "炮",
    (SOLDIER, RED): "兵",
    (KING, BLACK): "将", (ADVISOR, BLACK): "士", (ELEPHANT, BLACK): "象",
    (HORSE, BLACK): "马", (ROOK, BLACK): "车", (CANNON, BLACK): "砲",
    (SOLDIER, BLACK): "卒",
}

_FEN_MAP = {
    "k": KING, "a": ADVISOR, "e": ELEPHANT, "h": HORSE, "n": HORSE,
    "r": ROOK, "c": CANNON, "p": SOLDIER,
}
_FEN_RMAP = {
    KING: "k", ADVISOR: "a", ELEPHANT: "e", HORSE: "h",
    ROOK: "r", CANNON: "c", SOLDIER: "p",
}


@dataclass(frozen=True)
class Move:
    fr: int
    fc: int
    tr: int
    tc: int

    def valid(self) -> bool:
        return -1 not in (self.fr, self.fc, self.tr, self.tc)


@dataclass(frozen=True)
class Piece:
    type: int = NONE
    color: int = RED

    def empty(self) -> bool:
        return self.type == NONE


def in_palace(r: int, c: int, color: int) -> bool:
    """九宫：红方（下）row 7..9，黑方（上）row 0..2，列 3..5。"""
    if c < 3 or c > 5:
        return False
    return (7 <= r <= 9) if color == RED else (0 <= r <= 2)


def crossed_river(r: int, color: int) -> bool:
    """过河判断：红兵进入黑区(row<5)，黑兵进入红区(row>4)。"""
    return r < 5 if color == RED else r > 4


class Board:
    def __init__(self) -> None:
        self.grid: List[List[Piece]] = [[Piece() for _ in range(COLS)] for _ in range(ROWS)]
        self.red_turn: bool = True
        self.reset()

    # ---------- 布局 ----------
    def reset(self) -> None:
        g = self.grid
        for r in range(ROWS):
            for c in range(COLS):
                g[r][c] = Piece()
        back = [ROOK, HORSE, ELEPHANT, ADVISOR, KING, ADVISOR, ELEPHANT, HORSE, ROOK]
        for c, t in enumerate(back):
            g[0][c] = Piece(t, BLACK)
            g[9][c] = Piece(t, RED)
        g[2][1] = Piece(CANNON, BLACK)
        g[2][7] = Piece(CANNON, BLACK)
        g[7][1] = Piece(CANNON, RED)
        g[7][7] = Piece(CANNON, RED)
        for c in range(0, COLS, 2):
            g[3][c] = Piece(SOLDIER, BLACK)
            g[6][c] = Piece(SOLDIER, RED)
        self.red_turn = True

    def load_fen(self, fen: str) -> bool:
        board_part = fen.split(" ", 1)[0]
        for r in range(ROWS):
            for c in range(COLS):
                self.grid[r][c] = Piece()
        r = c = 0
        for ch in board_part:
            if ch == "/":
                r += 1
                c = 0
            elif ch.isdigit():
                c += int(ch)
            elif ch.lower() in _FEN_MAP and c < COLS:
                t = _FEN_MAP[ch.lower()]
                self.grid[r][c] = Piece(t, RED if ch.isupper() else BLACK)
                c += 1
        self.red_turn = True
        return True

    def fen(self) -> str:
        out = []
        for r in range(ROWS):
            empty = 0
            for c in range(COLS):
                p = self.grid[r][c]
                if p.empty():
                    empty += 1
                    continue
                if empty:
                    out.append(str(empty))
                    empty = 0
                ch = _FEN_RMAP[p.type]
                out.append(ch.upper() if p.color == RED else ch)
            if empty:
                out.append(str(empty))
            if r < ROWS - 1:
                out.append("/")
        out.append(" w" if self.red_turn else " b")
        return "".join(out)

    # ---------- 查询 ----------
    def piece_at(self, r: int, c: int) -> Piece:
        return self.grid[r][c]

    def is_red_turn(self) -> bool:
        return self.red_turn

    def king_pos(self, color: int) -> Optional[Tuple[int, int]]:
        for r in range(ROWS):
            for c in range(COLS):
                p = self.grid[r][c]
                if p.type == KING and p.color == color:
                    return r, c
        return None

    # ---------- 将军判定 ----------
    def is_in_check(self, color: int) -> bool:
        kp = self.king_pos(color)
        if kp is None:
            return False
        kr, kc = kp
        g = self.grid
        # 车/炮/将帅对脸（四条直线）
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c, blockers = kr + dr, kc + dc, 0
            while 0 <= r < ROWS and 0 <= c < COLS:
                p = g[r][c]
                if not p.empty():
                    if blockers == 0:
                        if p.color != color and p.type in (ROOK, KING):
                            return True
                    elif blockers == 1 and p.color != color and p.type == CANNON:
                        return True
                    blockers += 1
                    if blockers > 1:
                        break
                r += dr
                c += dc
        # 马（日字 + 蹩腿）
        horse_moves = [
            (-2, -1, -1, 0), (-2, 1, -1, 0), (-1, 2, 0, 1), (1, 2, 0, 1),
            (2, 1, 1, 0), (2, -1, 1, 0), (1, -2, 0, -1), (-1, -2, 0, -1),
        ]
        for hr, hc, lr, lc in horse_moves:
            r, c = kr + hr, kc + hc
            if 0 <= r < ROWS and 0 <= c < COLS:
                p = g[r][c]
                if p.color != color and p.type == HORSE and g[kr + lr][kc + lc].empty():
                    return True
        # 兵/卒
        direction = -1 if color == RED else 1
        r, c = kr + direction, kc
        if 0 <= r < ROWS and 0 <= c < COLS:
            p = g[r][c]
            if p.color != color and p.type == SOLDIER:
                return True
        for dc in (-1, 1):
            r, c = kr, kc + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                p = g[r][c]
                if p.color != color and p.type == SOLDIER and crossed_river(r, p.color):
                    return True
        return False

    # ---------- 伪合法走法生成（不含送将过滤） ----------
    def pseudo_moves(self, r: int, c: int) -> List[Move]:
        g = self.grid
        p = g[r][c]
        if p.empty():
            return []
        color = p.color
        moves: List[Move] = []

        def add(tr: int, tc: int) -> None:
            if 0 <= tr < ROWS and 0 <= tc < COLS:
                dst = g[tr][tc]
                if dst.empty() or dst.color != color:
                    moves.append(Move(r, c, tr, tc))

        t = p.type
        if t == KING:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                tr, tc = r + dr, c + dc
                if in_palace(tr, tc, color):
                    add(tr, tc)
        elif t == ADVISOR:
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                tr, tc = r + dr, c + dc
                if in_palace(tr, tc, color):
                    add(tr, tc)
        elif t == ELEPHANT:
            for dr, dc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
                tr, tc = r + dr, c + dc
                if not (0 <= tr < ROWS and 0 <= tc < COLS):
                    continue
                if crossed_river(tr, color):
                    continue
                if not g[r + dr // 2][c + dc // 2].empty():  # 塞象眼
                    continue
                add(tr, tc)
        elif t == HORSE:
            horse_moves = [
                (-2, -1, -1, 0), (-2, 1, -1, 0), (-1, 2, 0, 1), (1, 2, 0, 1),
                (2, 1, 1, 0), (2, -1, 1, 0), (1, -2, 0, -1), (-1, -2, 0, -1),
            ]
            for hr, hc, lr, lc in horse_moves:
                tr, tc = r + hr, c + hc
                if not (0 <= tr < ROWS and 0 <= tc < COLS):
                    continue
                if not g[r + lr][c + lc].empty():  # 蹩马腿
                    continue
                add(tr, tc)
        elif t in (ROOK, CANNON):
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if t == ROOK:
                    while 0 <= rr < ROWS and 0 <= cc < COLS and g[rr][cc].empty():
                        moves.append(Move(r, c, rr, cc))
                        rr += dr
                        cc += dc
                    if 0 <= rr < ROWS and 0 <= cc < COLS and g[rr][cc].color != color:
                        moves.append(Move(r, c, rr, cc))
                else:  # 炮：移动同车；吃子需恰好一个炮架
                    jumped = False
                    while 0 <= rr < ROWS and 0 <= cc < COLS:
                        if g[rr][cc].empty():
                            if not jumped:
                                moves.append(Move(r, c, rr, cc))
                        elif not jumped:
                            jumped = True
                        else:
                            if g[rr][cc].color != color:
                                moves.append(Move(r, c, rr, cc))
                            break
                        rr += dr
                        cc += dc
        elif t == SOLDIER:
            fwd = -1 if color == RED else 1
            add(r + fwd, c)
            if crossed_river(r, color):
                add(r, c - 1)
                add(r, c + 1)
        return moves

    def generate_moves(self, color: int) -> List[Move]:
        """生成全部合法走法（过滤走完导致己方被将军的走法）。"""
        result: List[Move] = []
        for r in range(ROWS):
            for c in range(COLS):
                p = self.grid[r][c]
                if p.empty() or p.color != color:
                    continue
                for m in self.pseudo_moves(r, c):
                    captured = self.grid[m.tr][m.tc]
                    self._apply(m)
                    if not self.is_in_check(color):
                        result.append(m)
                    self._unapply(m, captured)
        return result

    # ---------- 走子/撤销 ----------
    def _apply(self, m: Move) -> Piece:
        captured = self.grid[m.tr][m.tc]
        self.grid[m.tr][m.tc] = self.grid[m.fr][m.fc]
        self.grid[m.fr][m.fc] = Piece()
        self.red_turn = not self.red_turn
        return captured

    def _unapply(self, m: Move, captured: Piece) -> None:
        self.grid[m.fr][m.fc] = self.grid[m.tr][m.tc]
        self.grid[m.tr][m.tc] = captured
        self.red_turn = not self.red_turn

    def make_move(self, m: Move, color: int) -> Optional[Piece]:
        """合法则走子并返回被吃棋子（可能为空 Piece），非法返回 None。"""
        if not (0 <= m.fr < ROWS and 0 <= m.fc < COLS and 0 <= m.tr < ROWS and 0 <= m.tc < COLS):
            return None
        src = self.grid[m.fr][m.fc]
        if src.empty() or src.color != color:
            return None
        if not any(m == pm for pm in self.pseudo_moves(m.fr, m.fc)):
            return None
        captured = self._apply(m)
        if self.is_in_check(color):
            self._unapply(m, captured)
            return None
        return captured

    def undo_move(self, m: Move, captured: Piece) -> None:
        self._unapply(m, captured)

    def has_no_legal_moves(self, color: int) -> bool:
        return not self.generate_moves()
