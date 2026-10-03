"""engine.py — AI 引擎：子力/位置评估 + minimax + alpha-beta 剪枝 + 走法排序。"""

from __future__ import annotations

from typing import List, Optional

from .board import (
    ADVISOR, BLACK, Board, CANNON, ELEPHANT, HORSE, KING, Move, RED, ROOK, SOLDIER,
)

PIECE_VALUE = {
    KING: 100000, ROOK: 900, CANNON: 450, HORSE: 400,
    ELEPHANT: 200, ADVISOR: 200, SOLDIER: 100,
}

MATE = 100000
INF = 1_000_000


def position_bonus(t: int, color: int, r: int, c: int) -> int:
    bonus = 0
    if t == SOLDIER:
        if color == RED:
            if r < 5:
                bonus += 60
            if r <= 2:
                bonus += 40
        else:
            if r > 4:
                bonus += 60
            if r >= 7:
                bonus += 40
    elif t in (HORSE, CANNON):
        if 3 <= r <= 6 and 2 <= c <= 6:
            bonus += 10
    return bonus


class Engine:
    def evaluate(self, board: Board, color: int) -> int:
        score = 0
        for r in range(10):
            row = board.grid[r]
            for c in range(9):
                p = row[c]
                if p.empty():
                    continue
                v = PIECE_VALUE[p.type] + position_bonus(p.type, p.color, r, c)
                score += v if p.color == RED else -v
        return score if color == RED else -score

    def _move_score(self, board: Board, m: Move) -> int:
        dst = board.piece_at(m.tr, m.tc)
        if dst.empty():
            return 0
        return PIECE_VALUE[dst.type] * 10 - PIECE_VALUE[board.piece_at(m.fr, m.fc).type]

    def _sorted_moves(self, board: Board, color: int) -> List[Move]:
        moves = board.generate_moves(color)
        moves.sort(key=lambda m: self._move_score(board, m), reverse=True)
        return moves

    def search(self, board: Board, depth: int, alpha: int, beta: int,
               color: int, ply: int) -> int:
        if depth == 0:
            return self.evaluate(board, color)
        moves = self._sorted_moves(board, color)
        if not moves:
            return -MATE + ply  # 无合法走法：将死或困毙，均判负
        best = -INF
        for m in moves:
            captured = board.make_move(m, color)
            if captured is None:
                continue
            val = -self.search(board, depth - 1, -beta, -alpha,
                               BLACK if color == RED else RED, ply + 1)
            board.undo_move(m, captured)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    def best_move(self, board: Board, color: int, depth: int = 3) -> Optional[Move]:
        moves = self._sorted_moves(board, color)
        if not moves:
            return None
        best: Optional[Move] = None
        best_val = -INF
        alpha = -INF
        beta = INF
        for m in moves:
            captured = board.make_move(m, color)
            if captured is None:
                continue
            val = -self.search(board, depth - 1, -beta, -alpha,
                               BLACK if color == RED else RED, 1)
            board.undo_move(m, captured)
            if val > best_val:
                best_val = val
                best = m
            if val > alpha:
                alpha = val
        return best
