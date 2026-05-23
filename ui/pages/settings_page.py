import os
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QComboBox,
    QCheckBox, QSpinBox, QFileDialog, QMessageBox,
    QListView
)
from PyQt5.QtCore import Qt
import webbrowser

from ui.styles import COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_ACCENT


class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config.json"
        )
        self._config = self._load_config()
        self._init_ui()

    def _load_config(self):
        default = {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads", "manga"),
            "image_format": "jpg",
            "concurrent_downloads": 3,
            "auto_checkin": False,
            "auto_share": False,
            "sessdata": "",
            "bili_jct": "",
            "dede_user_id": "",
        }
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    default.update(saved)
            except Exception:
                pass
        return default

    def _save_config(self):
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def _make_row(self, label_text, widget, extra_widget=None):
        row = QHBoxLayout()
        row.setSpacing(12)
        label = QLabel(label_text)
        label.setMinimumWidth(80)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet("color: #9DA0BE; font-size: 13px; background: transparent;")
        row.addWidget(label)
        row.addWidget(widget, stretch=1)
        if extra_widget:
            row.addWidget(extra_widget)
        return row

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        account_group = QGroupBox("账号设置")
        account_layout = QVBoxLayout(account_group)
        account_layout.setSpacing(14)
        account_layout.setContentsMargins(20, 28, 20, 16)

        self.sess_input = QLineEdit()
        self.sess_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.sess_input.setPlaceholderText("输入B站 SESSDATA")
        self.sess_input.setMinimumHeight(38)
        self.sess_input.setMinimumWidth(200)
        self.sess_input.setText(self._config.get("sessdata", ""))
        account_layout.addLayout(self._make_row("SESSDATA", self.sess_input))

        self.jct_input = QLineEdit()
        self.jct_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.jct_input.setPlaceholderText("输入 bili_jct（可选）")
        self.jct_input.setMinimumHeight(38)
        self.jct_input.setMinimumWidth(200)
        self.jct_input.setText(self._config.get("bili_jct", ""))
        account_layout.addLayout(self._make_row("bili_jct", self.jct_input))

        self.dede_input = QLineEdit()
        self.dede_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.dede_input.setPlaceholderText("输入 DedeUserID")
        self.dede_input.setMinimumHeight(38)
        self.dede_input.setMinimumWidth(200)
        self.dede_input.setText(self._config.get("dede_user_id", ""))
        account_layout.addLayout(self._make_row("DedeUserID", self.dede_input))

        self.account_status = QLabel("")
        self.account_status.setAlignment(Qt.AlignCenter)
        self.account_status.setWordWrap(True)
        account_layout.addWidget(self.account_status)

        verify_btn_row = QHBoxLayout()
        verify_btn_row.addStretch()
        verify_btn = QPushButton("验证账号")
        verify_btn.setObjectName("primary_btn")
        verify_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.setMinimumWidth(100)
        verify_btn.setMinimumHeight(34)
        verify_btn.clicked.connect(self._on_verify_account)
        verify_btn_row.addWidget(verify_btn)
        verify_btn_row.addStretch()
        account_layout.addLayout(verify_btn_row)

        layout.addWidget(account_group)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #4E5072;")
        layout.addWidget(sep1)

        download_group = QGroupBox("下载设置")
        download_layout = QVBoxLayout(download_group)
        download_layout.setSpacing(14)
        download_layout.setContentsMargins(20, 28, 20, 16)

        self.path_input = QLineEdit()
        self.path_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.path_input.setText(self._config.get("download_path", ""))
        self.path_input.setMinimumHeight(38)
        self.path_input.setMinimumWidth(200)
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setMinimumWidth(60)
        browse_btn.setMinimumHeight(34)
        browse_btn.clicked.connect(self._on_browse_path)
        download_layout.addLayout(self._make_row("保存路径", self.path_input, browse_btn))

        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet("QComboBox { background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; min-height: 24px; border-radius: 8px; color: #E8E9F0; } QComboBox::drop-down { border: none; width: 30px; padding-right: 8px; background-color: #2D2F4A; } QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #9DA0BE; margin-right: 8px; }")
        self.format_combo.addItems(["jpg", "webp"])
        self.format_combo.setMinimumHeight(36)
        combo_view = QListView()
        combo_view.setStyleSheet("""
            QListView {
                background-color: #2D2F4A;
                border: 1px solid #4E5072;
                border-radius: 8px;
                outline: none;
                color: #E8E9F0;
            }
            QListView::item {
                padding: 8px 16px;
                min-height: 32px;
                color: #E8E9F0;
                background-color: #2D2F4A;
            }
            QListView::item:hover {
                background-color: #2A2C45;
                color: #FFFFFF;
            }
            QListView::item:selected {
                background-color: #6C5CE7;
                color: #FFFFFF;
            }
        """)
        self.format_combo.setView(combo_view)
        fmt = self._config.get("image_format", "jpg")
        idx = self.format_combo.findText(fmt)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        download_layout.addLayout(self._make_row("图片格式", self.format_combo))

        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(self._config.get("concurrent_downloads", 3))
        self.concurrent_spin.setMinimumHeight(36)
        self.concurrent_spin.setMinimumWidth(80)
        self.concurrent_spin.setMaximumWidth(120)
        download_layout.addLayout(self._make_row("并发数", self.concurrent_spin))

        layout.addWidget(download_group)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #4E5072;")
        layout.addWidget(sep2)

        auto_group = QGroupBox("自动化")
        auto_layout = QVBoxLayout(auto_group)
        auto_layout.setSpacing(12)
        auto_layout.setContentsMargins(20, 28, 20, 16)

        cb_style = """
            QCheckBox {
                spacing: 10px;
                font-size: 13px;
                color: #E8E9F0;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4E5072;
                background-color: #2D2F4A;
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border-color: #6C5CE7;
                background-color: #2A2C45;
            }
            QCheckBox::indicator:checked {
                background-color: #6C5CE7;
                border-color: #6C5CE7;
                image: none;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #4E5072;
                background-color: #2D2F4A;
            }
        """

        self.auto_checkin_cb = QCheckBox("启动时自动签到")
        self.auto_checkin_cb.setChecked(self._config.get("auto_checkin", False))
        self.auto_checkin_cb.setStyleSheet(cb_style)
        auto_layout.addWidget(self.auto_checkin_cb)

        self.auto_share_cb = QCheckBox("启动时自动分享漫画")
        self.auto_share_cb.setChecked(self._config.get("auto_share", False))
        self.auto_share_cb.setStyleSheet(cb_style)
        auto_layout.addWidget(self.auto_share_cb)

        layout.addWidget(auto_group)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setFixedHeight(1)
        sep3.setStyleSheet("background-color: #4E5072;")
        layout.addWidget(sep3)

        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        about_layout.setSpacing(8)
        about_layout.setContentsMargins(20, 28, 20, 16)

        about_name = QLabel("MangaHunter - 漫画猎手")
        about_name.setObjectName("card_title")
        about_layout.addWidget(about_name)

        about_ver = QLabel("版本 1.0.0")
        about_ver.setObjectName("subtitle_label")
        about_layout.addWidget(about_ver)

        about_desc = QLabel("B站漫画浏览与下载工具")
        about_desc.setObjectName("subtitle_label")
        about_desc.setWordWrap(True)
        about_layout.addWidget(about_desc)

        sep_authors = QFrame()
        sep_authors.setFrameShape(QFrame.HLine)
        sep_authors.setFixedHeight(1)
        sep_authors.setStyleSheet("background-color: #4E5072;")
        about_layout.addWidget(sep_authors)

        author_title = QLabel("作者")
        author_title.setStyleSheet("color: #6C5CE7; font-size: 14px; font-weight: 700; background: transparent;")
        about_layout.addWidget(author_title)

        author1 = QLabel("寒烟似雪  QQ: 2273962061")
        author1.setStyleSheet("color: #E8E9F0; font-size: 13px; background: transparent;")
        about_layout.addWidget(author1)

        author2 = QLabel("逸雨  QQ: 3241417097")
        author2.setStyleSheet("color: #E8E9F0; font-size: 13px; background: transparent;")
        about_layout.addWidget(author2)

        blog_btn = QPushButton("个人网站: www.myblog.ink")
        blog_btn.setObjectName("link_btn")
        blog_btn.setCursor(Qt.PointingHandCursor)
        blog_btn.clicked.connect(lambda: webbrowser.open("https://www.myblog.ink"))
        about_layout.addWidget(blog_btn)

        bili_btn = QPushButton("B站: 不会玩python的man")
        bili_btn.setObjectName("link_btn")
        bili_btn.setCursor(Qt.PointingHandCursor)
        bili_btn.clicked.connect(lambda: webbrowser.open("https://space.bilibili.com/3546841002019157"))
        about_layout.addWidget(bili_btn)

        layout.addWidget(about_group)

        layout.addStretch(1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.reset_btn = QPushButton("重 置")
        self.reset_btn.setObjectName("secondary_btn")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setMinimumWidth(80)
        self.reset_btn.setMinimumHeight(34)
        self.reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("保存设置")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setMinimumHeight(34)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _on_browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if path:
            self.path_input.setText(path)

    def _on_verify_account(self):
        sessdata = self.sess_input.text().strip()
        if not sessdata:
            self.account_status.setText("请输入 SESSDATA")
            self.account_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
            return
        self.account_status.setText("验证中...")
        self.account_status.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")

    def _on_save(self):
        self._config["sessdata"] = self.sess_input.text().strip()
        self._config["bili_jct"] = self.jct_input.text().strip()
        self._config["dede_user_id"] = self.dede_input.text().strip()
        self._config["download_path"] = self.path_input.text().strip()
        self._config["image_format"] = self.format_combo.currentText()
        self._config["concurrent_downloads"] = self.concurrent_spin.value()
        self._config["auto_checkin"] = self.auto_checkin_cb.isChecked()
        self._config["auto_share"] = self.auto_share_cb.isChecked()
        if self._save_config():
            QMessageBox.information(self, "成功", "设置已保存")
        else:
            QMessageBox.warning(self, "错误", "保存设置失败")

    def _on_reset(self):
        reply = QMessageBox.question(
            self, "确认", "确定要重置所有设置吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.sess_input.clear()
            self.jct_input.clear()
            self.dede_input.clear()
            self.path_input.setText(
                os.path.join(os.path.expanduser("~"), "Downloads", "manga")
            )
            self.format_combo.setCurrentIndex(0)
            self.concurrent_spin.setValue(3)
            self.auto_checkin_cb.setChecked(False)
            self.auto_share_cb.setChecked(False)
