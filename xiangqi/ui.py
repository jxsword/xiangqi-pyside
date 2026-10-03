"""ui.py — QWidget 自绘棋盘界面（QPainter 绘制棋盘、棋子与交互）。"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPen, QRadialGradient, QAction,
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .board import BLACK, RED, ROWS, COLS
from .game import GameState, PVE, PVP

# 配色（木纹棋盘 + 红黑棋子）
BOARD_BG = QColor(245, 222, 179)
LINE_COLOR = QColor(90, 60, 30)
RED_COLOR = QColor(200, 30, 30)
BLACK_COLOR = QColor(35, 35, 35)
SELECT_COLOR = QColor(255, 170, 0)
HINT_COLOR = QColor(60, 140, 60, 150)


class BoardWidget(QWidget):
    def __init__(self, game: GameState, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.game = game
        self.setMinimumSize(540, 600)
        self.margin = 36

    def _metrics(self):
        w, h = self.width(), self.height()
        cell_w = (w - 2 * self.margin) / (COLS - 1)
        cell_h = (h - 2 * self.margin) / (ROWS - 1)
        cell = min(cell_w, cell_h)
        board_w = cell * (COLS - 1)
        board_h = cell * (ROWS - 1)
        ox = (w - board_w) / 2
        oy = (h - board_h) / 2
        return cell, ox, oy

    def _center(self, r: int, c: int):
        cell, ox, oy = self._metrics()
        return QPointF(ox + c * cell, oy + r * cell)

    def _hit_test(self, pos):
        cell, ox, oy = self._metrics()
        c = round((pos.x() - ox) / cell)
        r = round((pos.y() - oy) / cell)
        if 0 <= r < ROWS and 0 <= c < COLS:
            center = self._center(r, c)
            if (pos - center).manhattanLength() <= cell * 0.8:
                return r, c
        return None

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        hit = self._hit_test(event.position())
        if hit is not None:
            self.game.click(*hit)
            self.window().refresh()
            # 人机模式：玩家走完后异步让 AI 思考，避免阻塞界面
            if (self.game.mode == PVE and not self.game.game_over
                    and not self.game.board.is_red_turn()):
                self.window().schedule_ai()

    # ---------- 绘制 ----------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), BOARD_BG)
        cell, ox, oy = self._metrics()
        pen = QPen(LINE_COLOR, 2)
        painter.setPen(pen)

        # 横线（10 条）
        for r in range(ROWS):
            y = oy + r * cell
            painter.drawLine(QPointF(ox, y), QPointF(ox + (COLS - 1) * cell, y))
        # 竖线（9 条；河界处两侧边线贯通，中间 7 条断开）
        for c in range(COLS):
            x = ox + c * cell
            if c == 0 or c == COLS - 1:
                painter.drawLine(QPointF(x, oy), QPointF(x, oy + (ROWS - 1) * cell))
            else:
                painter.drawLine(QPointF(x, oy), QPointF(x, oy + 4 * cell))
                painter.drawLine(QPointF(x, oy + 5 * cell),
                                 QPointF(x, oy + (ROWS - 1) * cell))
        # 九宫斜线
        painter.drawLine(QPointF(ox + 3 * cell, oy), QPointF(ox + 5 * cell, oy + 2 * cell))
        painter.drawLine(QPointF(ox + 5 * cell, oy), QPointF(ox + 3 * cell, oy + 2 * cell))
        painter.drawLine(QPointF(ox + 3 * cell, oy + 7 * cell),
                         QPointF(ox + 5 * cell, oy + 9 * cell))
        painter.drawLine(QPointF(ox + 5 * cell, oy + 7 * cell),
                         QPointF(ox + 3 * cell, oy + 9 * cell))
        # 楚河汉界
        painter.setFont(QFont(self.font().family(), int(cell * 0.42), QFont.Weight.Bold))
        river_top = oy + 4 * cell
        river_h = cell
        painter.drawText(QRectF(ox, river_top, (COLS - 1) * cell, river_h),
                         Qt.AlignmentFlag.AlignCenter, "楚 河            漢 界")
        # 炮位/兵位标记
        self._draw_position_marks(painter, cell, ox, oy)

        # 合法落点提示
        for m in self.game.legal_targets:
            center = self._center(m.tr, m.tc)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(HINT_COLOR))
            painter.drawEllipse(center, cell * 0.12, cell * 0.12)

        # 棋子
        radius = cell * 0.42
        for r in range(ROWS):
            for c in range(COLS):
                text = self.game.display_at(r, c)
                if not text:
                    continue
                center = self._center(r, c)
                self._draw_piece(painter, center, radius, text,
                                 self.game.piece_color_at(r, c),
                                 selected=(self.game.selected == (r, c)))
        painter.end()

    def _draw_position_marks(self, painter, cell, ox, oy) -> None:
        """炮位与兵卒位的十字小标记。"""
        pen = QPen(LINE_COLOR, 1.5)
        painter.setPen(pen)
        d = cell * 0.12
        gap = cell * 0.06
        points = [(2, 1), (2, 7), (7, 1), (7, 7)]
        points += [(3, c) for c in range(0, COLS, 2)]
        points += [(6, c) for c in range(0, COLS, 2)]
        for r, c in points:
            x, y = ox + c * cell, oy + r * cell
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                if (c == 0 and sx < 0) or (c == COLS - 1 and sx > 0):
                    continue
                x0 = x + sx * gap
                y0 = y + sy * gap
                painter.drawLine(QPointF(x0, y0), QPointF(x0 + sx * d, y0))
                painter.drawLine(QPointF(x0, y0), QPointF(x0, y0 + sy * d))

    def _draw_piece(self, painter, center, radius, text, color, selected) -> None:
        # 阴影
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 45)))
        painter.drawEllipse(center + QPointF(2, 3), radius, radius)
        # 棋子本体（米白渐变）
        grad = QRadialGradient(center - QPointF(radius * 0.3, radius * 0.3), radius * 1.2)
        grad.setColorAt(0, QColor(255, 250, 235))
        grad.setColorAt(1, QColor(228, 205, 160))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(120, 85, 40), 1.5))
        painter.drawEllipse(center, radius, radius)
        # 内圈
        painter.setPen(QPen(RED_COLOR if color == RED else BLACK_COLOR, 1.5))
        painter.drawEllipse(center, radius * 0.82, radius * 0.82)
        # 选中高亮
        if selected:
            painter.setPen(QPen(SELECT_COLOR, 3))
            painter.drawEllipse(center, radius * 1.05, radius * 1.05)
        # 汉字
        painter.setPen(QPen(RED_COLOR if color == RED else BLACK_COLOR, 1))
        f = QFont(self.font().family(), int(radius * 0.95), QFont.Weight.Bold)
        painter.setFont(f)
        painter.drawText(QRectF(center.x() - radius, center.y() - radius,
                                radius * 2, radius * 2),
                         Qt.AlignmentFlag.AlignCenter, text)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.game = GameState(mode=PVP, ai_depth=3)
        self.setWindowTitle("中国象棋（PySide6）")
        self._build_ui()
        self._ai_timer = QTimer(self)
        self._ai_timer.setSingleShot(True)
        self._ai_timer.timeout.connect(self._do_ai)
        self.refresh()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        bar = QHBoxLayout()

        self.btn_pvp = QPushButton("双人对战")
        self.btn_pve = QPushButton("人机对战")
        self.btn_undo = QPushButton("悔棋")
        self.depth_box = QComboBox()
        self.depth_box.addItems(["AI 难度：浅(1)", "AI 难度：中(2)", "AI 难度：深(3)", "AI 难度：深(4)"])
        self.depth_box.setCurrentIndex(2)
        self.depth_box.currentIndexChanged.connect(self._on_depth)

        self.btn_pvp.clicked.connect(lambda: self._new_game(PVP))
        self.btn_pve.clicked.connect(lambda: self._new_game(PVE))
        self.btn_undo.clicked.connect(self._on_undo)

        for w in (self.btn_pvp, self.btn_pve, self.btn_undo, self.depth_box):
            bar.addWidget(w)
        bar.addStretch(1)
        layout.addLayout(bar)

        self.board_widget = BoardWidget(self.game)
        layout.addWidget(self.board_widget, stretch=1)

        self.status_mode = QLabel()
        self.status_turn = QLabel()
        status_bar = QHBoxLayout()
        status_bar.addWidget(self.status_mode)
        status_bar.addStretch(1)
        status_bar.addWidget(self.status_turn)
        status_frame = QFrame()
        status_frame.setLayout(status_bar)
        layout.addWidget(status_frame)

        self.setCentralWidget(central)
        self.resize(580, 700)

    def _on_depth(self, idx: int) -> None:
        self.game.ai_depth = idx + 1

    def _new_game(self, mode: str) -> None:
        self._ai_timer.stop()
        self.game.new_game(mode)
        self.refresh()

    def _on_undo(self) -> None:
        self._ai_timer.stop()
        self.game.undo()
        self.refresh()

    def schedule_ai(self) -> None:
        self._ai_timer.start(80)

    def _do_ai(self) -> None:
        self.game.ai_move()
        self.refresh()
        if self.game.game_over:
            winner = "红方" if self.game.winner == RED else "黑方"
            QMessageBox.information(self, "对局结束", f"{winner}胜！")

    def refresh(self) -> None:
        self.status_mode.setText("模式：" + self.game.mode_name())
        self.status_turn.setText(self.game.status_text())
        self.board_widget.update()
