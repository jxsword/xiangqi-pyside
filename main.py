"""main.py — 中国象棋（PySide6）程序入口。"""

import sys

from PySide6.QtWidgets import QApplication

from xiangqi.ui import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("中国象棋")
    app.setOrganizationName("Xiangqi")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
