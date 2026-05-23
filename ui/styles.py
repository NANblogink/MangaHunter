COLOR_BG = "#1E1F33"
COLOR_BG_SIDEBAR = "#1A1B2E"
COLOR_BG_HOVER = "#2A2C45"
COLOR_BG_PRESSED = "#2D2F4A"
COLOR_BG_CARD = "#252740"
COLOR_BG_INPUT = "#2D2F4A"

COLOR_TEXT_PRIMARY = "#E8E9F0"
COLOR_TEXT_SECONDARY = "#9DA0BE"
COLOR_TEXT_DISABLED = "#6B6E8A"
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_SIDEBAR = "#9DA0BE"

COLOR_BORDER = "#4E5072"
COLOR_BORDER_FOCUS = "#6C5CE7"
COLOR_BORDER_LIGHT = "#2F3148"

COLOR_ACCENT = "#6C5CE7"
COLOR_ACCENT_HOVER = "#7D6FF0"
COLOR_ACCENT_PRESSED = "#5A4BD1"
COLOR_ACCENT_LIGHT = "rgba(108, 92, 231, 0.15)"
COLOR_ACCENT_GRADIENT_START = "#6C5CE7"
COLOR_ACCENT_GRADIENT_END = "#A29BFE"

COLOR_SUCCESS = "#00D2A0"
COLOR_SUCCESS_LIGHT = "rgba(0, 210, 160, 0.10)"
COLOR_WARNING = "#FDCB6E"
COLOR_WARNING_DARK = "#E17055"
COLOR_ERROR = "#FF6B6B"
COLOR_ERROR_LIGHT = "rgba(255, 107, 107, 0.10)"

COLOR_SCROLLBAR_BG = "#1E1F33"
COLOR_SCROLLBAR_HANDLE = "#4A4C66"


def _build_stylesheet():
    parts = []
    a = parts.append

    a("QWidget {{ background-color: {}; color: {}; font-family: \"Microsoft YaHei UI\", \"Segoe UI\", sans-serif; border: none; outline: none; }}".format(COLOR_BG, COLOR_TEXT_PRIMARY))
    a("QMainWindow {{ background-color: {}; }}".format(COLOR_BG))
    a("QLabel {{ background: transparent; }}")

    a("QFrame#sidebar {{ background-color: {}; border-right: none; }}".format(COLOR_BG_SIDEBAR))

    a("QPushButton#nav_btn {{ background-color: transparent; color: {}; border: none; text-align: left; padding: 13px 22px; font-size: 14px; font-weight: 500; border-radius: 8px; margin: 2px 10px; }}".format(COLOR_TEXT_SIDEBAR))
    a("QPushButton#nav_btn:hover {{ background-color: {}; color: {}; }}".format(COLOR_BG_HOVER, COLOR_TEXT_WHITE))
    a("QPushButton#nav_btn[active=\"true\"] {{ background-color: {}; color: {}; font-weight: bold; }}".format(COLOR_ACCENT, COLOR_TEXT_WHITE))

    a("QPushButton#primary_btn {{ background-color: {}; color: {}; border: 2px solid {}; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px; }}".format(COLOR_ACCENT, COLOR_TEXT_WHITE, COLOR_ACCENT_HOVER))
    a("QPushButton#primary_btn:hover {{ background-color: {}; border-color: {}; }}".format(COLOR_ACCENT_HOVER, COLOR_ACCENT_HOVER))
    a("QPushButton#primary_btn:pressed {{ background-color: {}; border-color: {}; }}".format(COLOR_ACCENT_PRESSED, COLOR_ACCENT_PRESSED))
    a("QPushButton#primary_btn:disabled {{ background-color: {}; color: {}; border-color: {}; }}".format(COLOR_BG_PRESSED, COLOR_TEXT_DISABLED, COLOR_BORDER))

    a("QPushButton#secondary_btn {{ background-color: {}; color: {}; border: 2px solid {}; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px; }}".format(COLOR_BG_PRESSED, COLOR_ACCENT, COLOR_BORDER))
    a("QPushButton#secondary_btn:hover {{ background-color: {}; border-color: {}; color: {}; }}".format(COLOR_ACCENT_LIGHT, COLOR_ACCENT, COLOR_ACCENT))
    a("QPushButton#secondary_btn:pressed {{ background-color: {}; border-color: {}; }}".format(COLOR_BG_HOVER, COLOR_ACCENT))
    a("QPushButton#secondary_btn:disabled {{ background-color: {}; color: {}; border-color: {}; }}".format(COLOR_BG_PRESSED, COLOR_TEXT_DISABLED, COLOR_BORDER_LIGHT))

    a("QPushButton#icon_btn {{ background-color: transparent; border: 1px solid {}; padding: 8px; border-radius: 6px; }}".format(COLOR_BORDER))
    a("QPushButton#icon_btn:hover {{ background-color: {}; border-color: {}; }}".format(COLOR_BG_HOVER, COLOR_ACCENT))

    a("QPushButton#link_btn {{ background: transparent; color: {}; border: 1px solid transparent; padding: 4px 8px; font-size: 13px; border-radius: 4px; text-decoration: underline; }}".format(COLOR_ACCENT))
    a("QPushButton#link_btn:hover {{ background-color: {}; border-color: {}; color: {}; }}".format(COLOR_ACCENT_LIGHT, COLOR_ACCENT, COLOR_ACCENT_HOVER))

    a("QLineEdit {{ background-color: {}; border: 2px solid {}; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: {}; min-height: 24px; }}".format(COLOR_BG_INPUT, COLOR_BORDER, COLOR_TEXT_PRIMARY))
    a("QLineEdit:focus {{ border-color: {}; border-width: 2px; }}".format(COLOR_BORDER_FOCUS))
    a("QLineEdit:hover:!focus {{ border-color: {}; }}".format(COLOR_ACCENT))

    a("QTextEdit {{ background-color: {}; border: 2px solid {}; padding: 8px 12px; font-size: 13px; border-radius: 8px; color: {}; }}".format(COLOR_BG_INPUT, COLOR_BORDER, COLOR_TEXT_PRIMARY))
    a("QTextEdit:focus {{ border-color: {}; }}".format(COLOR_BORDER_FOCUS))

    a("QComboBox {{ background-color: {}; border: 2px solid {}; padding: 6px 12px; font-size: 13px; min-height: 24px; border-radius: 8px; color: {}; }}".format(COLOR_BG_INPUT, COLOR_BORDER, COLOR_TEXT_PRIMARY))
    a("QComboBox:focus {{ border-color: {}; }}".format(COLOR_BORDER_FOCUS))
    a("QComboBox::drop-down {{ border: none; width: 30px; padding-right: 8px; background-color: {}; }}".format(COLOR_BG_INPUT))
    a("QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid {}; margin-right: 8px; }}".format(COLOR_TEXT_SECONDARY))
    a("QComboBox QAbstractItemView {{ background-color: {}; border: 2px solid {}; selection-background-color: {}; selection-color: {}; outline: none; border-radius: 8px; color: {}; }}".format(COLOR_BG_INPUT, COLOR_BORDER, COLOR_ACCENT, COLOR_TEXT_WHITE, COLOR_TEXT_PRIMARY))
    a("QComboBox QAbstractItemView::item {{ padding: 8px 16px; min-height: 32px; color: {}; background-color: {}; }}".format(COLOR_TEXT_PRIMARY, COLOR_BG_INPUT))
    a("QComboBox QAbstractItemView::item:hover {{ background-color: {}; color: {}; }}".format(COLOR_BG_HOVER, COLOR_TEXT_WHITE))
    a("QComboBox QAbstractItemView::item:selected {{ background-color: {}; color: {}; }}".format(COLOR_ACCENT, COLOR_TEXT_WHITE))

    a("QListWidget {{ background-color: {}; border: 2px solid {}; outline: none; border-radius: 8px; color: {}; }}".format(COLOR_BG_CARD, COLOR_BORDER, COLOR_TEXT_PRIMARY))
    a("QListWidget::item {{ padding: 12px 16px; border-bottom: 1px solid {}; }}".format(COLOR_BORDER_LIGHT))
    a("QListWidget::item:hover {{ background-color: {}; }}".format(COLOR_ACCENT_LIGHT))
    a("QListWidget::item:selected {{ background-color: {}; color: {}; }}".format(COLOR_ACCENT, COLOR_TEXT_WHITE))

    a("QTableWidget {{ background-color: {}; border: 2px solid {}; gridline-color: {}; outline: none; alternate-background-color: #22233A; border-radius: 8px; color: {}; }}".format(COLOR_BG_CARD, COLOR_BORDER, COLOR_BORDER_LIGHT, COLOR_TEXT_PRIMARY))
    a("QTableWidget::item {{ padding: 8px 12px; border-bottom: 1px solid {}; }}".format(COLOR_BORDER_LIGHT))
    a("QTableWidget::item:hover {{ background-color: {}; }}".format(COLOR_ACCENT_LIGHT))
    a("QTableWidget::item:selected {{ background-color: {}; color: {}; }}".format(COLOR_ACCENT, COLOR_TEXT_WHITE))

    a("QHeaderView::section {{ background-color: {}; border: none; border-bottom: 2px solid {}; border-right: 1px solid {}; padding: 12px 14px; font-weight: 600; font-size: 12px; color: {}; letter-spacing: 0.5px; }}".format(COLOR_BG_PRESSED, COLOR_ACCENT, COLOR_BORDER_LIGHT, COLOR_TEXT_SECONDARY))

    a("QScrollBar:vertical {{ background-color: transparent; width: 6px; border: none; margin: 0px; }}".format())
    a("QScrollBar::handle:vertical {{ background-color: rgba(74, 76, 102, 0.5); min-height: 30px; border-radius: 3px; }}".format())
    a("QScrollBar::handle:vertical:hover {{ background-color: rgba(108, 92, 231, 0.6); }}".format())
    a("QScrollBar::handle:vertical:pressed {{ background-color: rgba(108, 92, 231, 0.8); }}".format())
    a("QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}")
    a("QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}")

    a("QScrollBar:horizontal {{ background-color: transparent; height: 6px; border: none; margin: 0px; }}".format())
    a("QScrollBar::handle:horizontal {{ background-color: rgba(74, 76, 102, 0.5); min-width: 30px; border-radius: 3px; }}".format())
    a("QScrollBar::handle:horizontal:hover {{ background-color: rgba(108, 92, 231, 0.6); }}".format())
    a("QScrollBar::handle:horizontal:pressed {{ background-color: rgba(108, 92, 231, 0.8); }}".format())
    a("QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}")
    a("QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}")

    a("QProgressBar {{ background-color: {}; border: 2px solid {}; text-align: center; height: 22px; font-size: 11px; font-weight: 600; border-radius: 11px; color: {}; }}".format(COLOR_BG_PRESSED, COLOR_BORDER, COLOR_TEXT_PRIMARY))
    a("QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {}, stop:1 {}); border-radius: 9px; }}".format(COLOR_ACCENT_GRADIENT_START, COLOR_ACCENT_GRADIENT_END))

    a("QCheckBox {{ spacing: 10px; font-size: 13px; color: {}; background: transparent; }}".format(COLOR_TEXT_PRIMARY))
    a("QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {}; background-color: {}; border-radius: 4px; }}".format(COLOR_BORDER, COLOR_BG_INPUT))
    a("QCheckBox::indicator:hover {{ border-color: {}; background-color: {}; }}".format(COLOR_ACCENT, COLOR_BG_HOVER))
    a("QCheckBox::indicator:checked {{ background-color: {}; border-color: {}; image: none; }}".format(COLOR_ACCENT, COLOR_ACCENT))
    a("QCheckBox::indicator:unchecked {{ border: 2px solid {}; background-color: {}; }}".format(COLOR_BORDER, COLOR_BG_INPUT))

    a("QLabel#title_label {{ font-size: 26px; font-weight: 700; color: {}; letter-spacing: 0.5px; background: transparent; }}".format(COLOR_TEXT_PRIMARY))
    a("QLabel#subtitle_label {{ font-size: 14px; color: {}; line-height: 1.5; background: transparent; }}".format(COLOR_TEXT_SECONDARY))
    a("QLabel#card_title {{ font-size: 15px; font-weight: 600; color: {}; background: transparent; }}".format(COLOR_TEXT_PRIMARY))
    a("QLabel#status_success {{ color: {}; font-weight: 600; background: transparent; }}".format(COLOR_SUCCESS))
    a("QLabel#status_error {{ color: {}; font-weight: 600; background: transparent; }}".format(COLOR_ERROR))
    a("QLabel#status_warning {{ color: {}; font-weight: 600; background: transparent; }}".format(COLOR_WARNING_DARK))

    a("QSplitter::handle {{ background-color: {}; }}".format(COLOR_BORDER))
    a("QSplitter::handle:horizontal {{ width: 1px; }}")
    a("QSplitter::handle:vertical {{ height: 1px; }}")

    a("QGroupBox {{ border: 2px solid {}; border-radius: 12px; margin-top: 16px; padding-top: 20px; font-weight: 600; font-size: 14px; color: {}; background-color: {}; }}".format(COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_BG_CARD))
    a("QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 4px 14px; color: {}; font-weight: 700; font-size: 14px; background-color: {}; border: 1px solid {}; border-radius: 6px; }}".format(COLOR_ACCENT, COLOR_BG_CARD, COLOR_BORDER))

    a("QTabWidget::pane {{ border: 2px solid {}; background-color: {}; border-radius: 8px; }}".format(COLOR_BORDER, COLOR_BG))
    a("QTabBar::tab {{ background-color: {}; border: 2px solid {}; padding: 10px 24px; margin-right: 2px; font-weight: 500; border-radius: 8px 8px 0 0; color: {}; }}".format(COLOR_BG_CARD, COLOR_BORDER, COLOR_TEXT_SECONDARY))
    a("QTabBar::tab:selected {{ background-color: {}; border-bottom-color: {}; color: {}; font-weight: bold; }}".format(COLOR_BG, COLOR_BG, COLOR_ACCENT))
    a("QTabBar::tab:hover:!selected {{ background-color: {}; }}".format(COLOR_BG_HOVER))

    a("QSpinBox {{ background-color: {}; border: 2px solid {}; padding: 4px 8px; border-radius: 8px; color: {}; min-height: 24px; }}".format(COLOR_BG_INPUT, COLOR_BORDER, COLOR_TEXT_PRIMARY))
    a("QSpinBox:focus {{ border-color: {}; }}".format(COLOR_BORDER_FOCUS))
    a("QSpinBox::up-button, QSpinBox::down-button {{ width: 24px; border-left: 1px solid {}; background: transparent; }}".format(COLOR_BORDER))
    a("QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background-color: {}; }}".format(COLOR_ACCENT_LIGHT))
    a("QSpinBox::up-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid {}; }}".format(COLOR_TEXT_SECONDARY))
    a("QSpinBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {}; }}".format(COLOR_TEXT_SECONDARY))

    a("QScrollArea {{ background: transparent; border: none; }}")

    a("QMessageBox {{ background-color: {}; }}".format(COLOR_BG_CARD))
    a("QMessageBox QLabel {{ color: {}; background: transparent; }}".format(COLOR_TEXT_PRIMARY))
    a("QMessageBox QPushButton {{ background-color: {}; color: {}; border: 2px solid {}; padding: 8px 24px; border-radius: 6px; min-width: 80px; }}".format(COLOR_ACCENT, COLOR_TEXT_WHITE, COLOR_ACCENT_HOVER))

    return "\n".join(parts)


STYLESHEET = _build_stylesheet()
