from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .views.main_window import MainWindow


class App:
    def __init__(self) -> None:
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.window = MainWindow()

    def exec(self) -> int:
        self.window.show()
        return self.qt_app.exec()


def run() -> int:
    return App().exec()
