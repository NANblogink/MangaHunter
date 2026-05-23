import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont, QIcon

from ui.main_window import MainWindow
from utils.logger import log


def main():
    log.info("=" * 50)
    log.info("MangaHunter - 漫画猎手 启动")
    log.info("=" * 50)

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    screen = app.primaryScreen()
    if screen:
        dpi = screen.logicalDotsPerInch()
        scale = dpi / 96.0
        log.info("屏幕DPI: %d, 缩放比例: %.2f", dpi, scale)
        if scale > 1.0:
            base_size = 9
            font.setPointSize(int(base_size * scale + 0.5))

    window = MainWindow()
    window.show()

    log.info("主窗口已显示")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
