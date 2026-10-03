"""test_rules.py — 规则引擎与 AI 单元测试（与 C++/QML 版同一组用例）。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xiangqi.board import BLACK, RED, Board, CANNON, HORSE, KING, ROOK  # noqa: E402
from xiangqi.engine import Engine  # noqa: E402


class RuleTests(unittest.TestCase):
    def test_01_initial_layout_and_fen(self):
        b = Board()
        self.assertEqual(b.piece_at(0, 0).type, ROOK)
        self.assertEqual(b.piece_at(0, 0).color, BLACK)
        self.assertEqual(b.piece_at(9, 4).type, KING)
        self.assertEqual(b.piece_at(9, 4).color, RED)
        self.assertTrue(b.fen().startswith("rheakaehr"))

    def test_02_first_move_count_44(self):
        b = Board()
        self.assertEqual(len(b.generate_moves(RED)), 44)

    def test_03_horse_jump(self):
        b = Board()
        moves = b.generate_moves(RED)
        self.assertTrue(any(m.fr == 9 and m.fc == 1 and m.tr == 7 and m.tc == 0
                            for m in moves))

    def test_04_hobbled_horse(self):
        b = Board()
        b.load_fen("4k4/9/9/4P4/4n4/9/9/9/9/4K4 w - - 0 1")
        moves = b.generate_moves(BLACK)
        # 马腿 (3,4) 被红兵挡住：(4,4)->(2,3) 与 (4,4)->(2,5) 均非法
        self.assertFalse(any(m.fr == 4 and m.fc == 4 and m.tr == 2 and m.tc == 3
                             for m in moves))
        self.assertFalse(any(m.fr == 4 and m.fc == 4 and m.tr == 2 and m.tc == 5
                             for m in moves))

    def test_05_kings_facing(self):
        b = Board()
        b.load_fen("4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1")
        moves = b.generate_moves(BLACK)
        self.assertFalse(any(m.fr == 0 and m.fc == 4 and m.tr == 1 and m.tc == 4
                             for m in moves))
        self.assertTrue(b.is_in_check(BLACK))

    def test_06_cannon_screen(self):
        b = Board()
        b.load_fen("4k4/9/2c6/9/9/9/2P6/9/2N6/5K3 w - - 0 1")
        self.assertTrue(any(m.fr == 2 and m.fc == 2 and m.tr == 8 and m.tc == 2
                            for m in b.generate_moves(BLACK)))
        b2 = Board()
        b2.load_fen("4k4/9/2c6/9/9/9/9/9/2N6/5K3 w - - 0 1")
        self.assertFalse(any(m.fr == 2 and m.fc == 2 and m.tr == 8 and m.tc == 2
                             for m in b2.generate_moves(BLACK)))

    def test_07_ai_best_move(self):
        b = Board()
        m = Engine().best_move(b, RED, 2)
        self.assertIsNotNone(m)
        self.assertTrue(m.valid())


if __name__ == "__main__":
    unittest.main(verbosity=2)
