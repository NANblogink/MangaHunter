from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QPushButton, QStackedWidget, QLabel,
    QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QCursor

from ui.styles import STYLESHEET, COLOR_BG_SIDEBAR, COLOR_ACCENT
from ui.pages.login_page import LoginPage
from ui.pages.search_page import SearchPage
from ui.pages.download_page import DownloadPage
from ui.pages.checkin_page import CheckinPage
from ui.pages.settings_page import SettingsPage
from api.config import get_login_credentials


class NavButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(parent)
        self.setObjectName("nav_btn")
        self.setText(f"  {text}")
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._active = False
        self._default_style = ""
        self._active_style = ""

    def set_active(self, active):
        self._active = active
        if active:
            self.setStyleSheet("""
                QPushButton#nav_btn {
                    background-color: #6C5CE7;
                    color: #FFFFFF;
                    border: none;
                    text-align: left;
                    padding: 13px 22px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 2px 10px;
                }
                QPushButton#nav_btn:hover {
                    background-color: #7D6FF0;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton#nav_btn {
                    background-color: transparent;
                    color: #9DA0BE;
                    border: none;
                    text-align: left;
                    padding: 13px 22px;
                    font-size: 14px;
                    font-weight: 500;
                    border-radius: 8px;
                    margin: 2px 10px;
                }
                QPushButton#nav_btn:hover {
                    background-color: #2A2C45;
                    color: #FFFFFF;
                }
            """)


class MainWindow(QMainWindow):
    EDGE_SIZE = 6

    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._resize_dir = None
        self._resize_start_geo = None
        self._resize_start_pos = None
        self._init_dpi()
        self._init_ui()
        self._apply_style()

    def _init_dpi(self):
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            self._scale = dpi / 96.0
        else:
            self._scale = 1.0
        if self._scale < 1.0:
            self._scale = 1.0

    def _sv(self, value):
        return int(value * self._scale)

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        self.setWindowTitle("MangaHunter - 漫画猎手")
        self.setMinimumSize(self._sv(1100), self._sv(750))
        self.resize(self._sv(1200), self._sv(800))

        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        body = QWidget()
        body.setObjectName("body_widget")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(self._sv(180))
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo_area = QFrame()
        logo_area.setStyleSheet("QFrame { background: transparent; }")
        logo_lay = QVBoxLayout(logo_area)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        logo_lay.setSpacing(0)

        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("QFrame { background: transparent; }")
        title_bar_lay = QHBoxLayout(title_bar)
        title_bar_lay.setContentsMargins(16, 0, 12, 0)
        title_bar_lay.setSpacing(0)

        app_icon = QLabel("M")
        app_icon.setFixedSize(22, 22)
        app_icon.setAlignment(Qt.AlignCenter)
        app_icon.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6C5CE7, stop:1 #A29BFE);
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        title_bar_lay.addWidget(app_icon)

        app_label = QLabel(" MangaHunter")
        app_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 700;
                color: #FFFFFF;
                background: transparent;
            }
        """)
        app_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_bar_lay.addWidget(app_label)
        title_bar_lay.addStretch()

        logo_lay.addWidget(title_bar)
        sidebar_layout.addWidget(logo_area)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(8)

        self.nav_buttons = []
        nav_items = [
            ("login", "登 录"),
            ("search", "搜 索"),
            ("download", "下 载"),
            ("checkin", "签 到"),
            ("settings", "设 置"),
        ]
        for key, text in nav_items:
            btn = NavButton(text)
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append((key, btn))

        sidebar_layout.addStretch(1)

        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(108, 92, 231, 0.12);
                border: none;
                border-radius: 8px;
                margin: 8px;
            }
        """)
        user_lay = QVBoxLayout(user_frame)
        user_lay.setContentsMargins(14, 10, 14, 10)
        user_lay.setSpacing(4)
        self.user_label = QLabel("未登录")
        self.user_label.setStyleSheet("color: #9DA0BE; font-size: 12px; background: transparent;")
        self.user_label.setWordWrap(True)
        self.user_label.setAlignment(Qt.AlignCenter)
        user_lay.addWidget(self.user_label)
        sidebar_layout.addWidget(user_frame)

        body_layout.addWidget(sidebar)

        content_area = QFrame()
        content_area.setObjectName("content_area")
        content_area.setStyleSheet("QFrame#content_area { background-color: #1E1F33; }")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_title_bar = QFrame()
        content_title_bar.setObjectName("content_title_bar")
        content_title_bar.setFixedHeight(40)
        content_title_bar.setStyleSheet("QFrame#content_title_bar { background-color: #2D2F4A; }")
        ctb_lay = QHBoxLayout(content_title_bar)
        ctb_lay.setContentsMargins(16, 0, 8, 0)
        ctb_lay.setSpacing(4)

        self.page_title_label = QLabel("登录")
        self.page_title_label.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600; background: transparent;")
        ctb_lay.addWidget(self.page_title_label)
        ctb_lay.addStretch()

        tb_btn_style = """
            QPushButton {{
                background: transparent;
                color: #9DA0BE;
                border: none;
                font-size: {font_size}px;
                border-radius: 4px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: {hover_color};
            }}
        """

        min_btn = QPushButton("—")
        min_btn.setFixedSize(40, 28)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setStyleSheet(tb_btn_style.format(font_size=12, hover_bg="#3D3F5A", hover_color="#FFFFFF"))
        min_btn.clicked.connect(self.showMinimized)
        ctb_lay.addWidget(min_btn)

        self._max_btn = QPushButton("□")
        self._max_btn.setFixedSize(40, 28)
        self._max_btn.setCursor(Qt.PointingHandCursor)
        self._max_btn.setStyleSheet(tb_btn_style.format(font_size=11, hover_bg="#3D3F5A", hover_color="#FFFFFF"))
        self._max_btn.clicked.connect(self._toggle_maximize)
        ctb_lay.addWidget(self._max_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(tb_btn_style.format(font_size=12, hover_bg="#FF6B6B", hover_color="white"))
        close_btn.clicked.connect(self.close)
        ctb_lay.addWidget(close_btn)

        content_layout.addWidget(content_title_bar)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.pages = {}
        self._page_titles = {
            "login": "登录",
            "search": "搜索漫画",
            "download": "下载管理",
            "checkin": "签到与任务",
            "settings": "设置",
        }
        for key, cls in [
            ("login", LoginPage),
            ("search", SearchPage),
            ("download", DownloadPage),
            ("checkin", CheckinPage),
            ("settings", SettingsPage),
        ]:
            page = cls(self)
            self.pages[key] = page
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        body_layout.addWidget(content_area, stretch=1)

        main_layout.addWidget(body)
        self._switch_page("login")

        creds = get_login_credentials()
        if creds.get("sessdata"):
            self.user_label.setText("验证中...")
            self.user_label.setStyleSheet("color: #FDCB6E; font-size: 12px; background: transparent;")

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self._max_btn.setText("□")
        else:
            self.showMaximized()
            self._max_btn.setText("❐")

    def _switch_page(self, key):
        for k, btn in self.nav_buttons:
            btn.set_active(k == key)
        if key in self.pages:
            page = self.pages[key]
            self.stack.setCurrentWidget(page)
            if hasattr(page, 'refresh'):
                page.refresh()
        title = self._page_titles.get(key, "")
        self.page_title_label.setText(title)

    def _apply_style(self):
        self.setStyleSheet(STYLESHEET + """
            #central_widget {
                background-color: #1A1B2E;
            }
            #body_widget {
                background-color: #1A1B2E;
            }
        """)

    def update_user_info(self, username=""):
        self.user_label.setText(username if username else "未登录")

    def get_scale(self):
        return self._scale

    def scale_value(self, value):
        return int(value * self._scale)

    def _edge_at(self, pos):
        rect = self.rect()
        e = self.EDGE_SIZE
        x, y = pos.x(), pos.y()

        on_left = x < e
        on_right = x > rect.width() - e
        on_top = y < e
        on_bottom = y > rect.height() - e

        if on_top and on_left:
            return "top_left"
        if on_top and on_right:
            return "top_right"
        if on_bottom and on_left:
            return "bottom_left"
        if on_bottom and on_right:
            return "bottom_right"
        if on_left:
            return "left"
        if on_right:
            return "right"
        if on_top:
            return "top"
        if on_bottom:
            return "bottom"
        return None

    def _cursor_for_edge(self, edge):
        cursors = {
            "left": Qt.SizeHorCursor,
            "right": Qt.SizeHorCursor,
            "top": Qt.SizeVerCursor,
            "bottom": Qt.SizeVerCursor,
            "top_left": Qt.SizeFDiagCursor,
            "bottom_right": Qt.SizeFDiagCursor,
            "top_right": Qt.SizeBDiagCursor,
            "bottom_left": Qt.SizeBDiagCursor,
        }
        return cursors.get(edge, Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._edge_at(event.pos())
            if edge:
                self._resize_dir = edge
                self._resize_start_geo = self.geometry()
                self._resize_start_pos = event.globalPos()
            else:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            edge = self._edge_at(event.pos())
            self.setCursor(self._cursor_for_edge(edge) if edge else Qt.ArrowCursor)
            return

        if self._resize_dir and self._resize_start_geo and self._resize_start_pos:
            delta = event.globalPos() - self._resize_start_pos
            geo = QRect(self._resize_start_geo)
            min_w = self.minimumWidth()
            min_h = self.minimumHeight()

            d = self._resize_dir
            if "left" in d:
                new_w = geo.width() - delta.x()
                if new_w >= min_w:
                    geo.setLeft(geo.left() + delta.x())
            if "right" in d:
                new_w = geo.width() + delta.x()
                if new_w >= min_w:
                    geo.setRight(geo.right() + delta.x())
            if "top" in d:
                new_h = geo.height() - delta.y()
                if new_h >= min_h:
                    geo.setTop(geo.top() + delta.y())
            if "bottom" in d:
                new_h = geo.height() + delta.y()
                if new_h >= min_h:
                    geo.setBottom(geo.bottom() + delta.y())

            self.setGeometry(geo)
            event.accept()
        elif self._drag_pos:
            if self.isMaximized():
                self.showNormal()
                self._max_btn.setText("□")
                ratio = event.pos().x() / self.width()
                self._drag_pos = QPoint(int(self.width() * ratio) - event.pos().x(), event.pos().y())
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_dir = None
        self._resize_start_geo = None
        self._resize_start_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowMaximized:
                self._max_btn.setText("❐")
            else:
                self._max_btn.setText("□")

    def closeEvent(self, event):
        for page in self.pages.values():
            if hasattr(page, 'closeEvent'):
                page.closeEvent(event)
            elif hasattr(page, '_stop_all_workers'):
                page._stop_all_workers()
        event.accept()
