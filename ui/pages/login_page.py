from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QGridLayout,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

from ui.styles import COLOR_ACCENT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_TEXT_PRIMARY
from api.bilibili_manga import BilibiliMangaAPI
from api.config import save_login_credentials, get_login_credentials, clear_login_credentials


class QRCodeWorker(QThread):
    qr_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api):
        super().__init__()
        self.api = api

    def run(self):
        result = self.api.get_qr_code()
        if result:
            self.qr_ready.emit(result)
        else:
            self.error.emit("获取二维码失败")


class QRCheckWorker(QThread):
    status_update = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, api, qrcode_key):
        super().__init__()
        self.api = api
        self.qrcode_key = qrcode_key
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            result = self.api.check_qr_status(self.qrcode_key)
            if result:
                status = result.get("status", "error")
                self.status_update.emit(result)
                if status == "success" or status == "error" or status == "expired":
                    break
            else:
                break
            self.msleep(1500)
        self.finished.emit()


class LoginVerifyWorker(QThread):
    verify_result = pyqtSignal(bool, str)

    def __init__(self, api):
        super().__init__()
        self.api = api

    def run(self):
        success = self.api.verify_login()
        if success and self.api.user_info:
            self.verify_result.emit(True, f"登录成功 - {self.api.user_info.get('uname', '用户')}")
        else:
            self.verify_result.emit(False, "验证失败，请检查SESSDATA")


class AvatarLoader(QThread):
    avatar_loaded = pyqtSignal(object)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            import requests as req
            resp = req.get(self.url, timeout=10)
            if resp.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(resp.content)
                if not pixmap.isNull():
                    self.avatar_loaded.emit(pixmap)
                    return
            self.avatar_loaded.emit(None)
        except Exception:
            self.avatar_loaded.emit(None)


class LoginPage(QWidget):
    login_success = pyqtSignal(dict)
    logout_signal = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.api = BilibiliMangaAPI()
        self._qr_worker = None
        self._qr_check_worker = None
        self._verify_worker = None
        self._avatar_loader = None
        self._qrcode_key = ""
        self._logged_in = False
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container.setMinimumWidth(900)
        lay = QVBoxLayout(container)
        lay.setContentsMargins(48, 36, 48, 36)
        lay.setSpacing(28)

        self.title_label = QLabel("登录")
        self.title_label.setObjectName("title_label")
        lay.addWidget(self.title_label)

        self.desc_label = QLabel("扫描二维码或输入 SESSDATA 登录B站账号")
        self.desc_label.setObjectName("subtitle_label")
        self.desc_label.setWordWrap(True)
        lay.addWidget(self.desc_label)

        self.user_card_frame = QFrame()
        self.user_card_frame.setObjectName("user_card")
        self.user_card_frame.setStyleSheet("""
            QFrame#user_card {
                background-color: #252740;
                border: 1px solid #4E5072;
                border-radius: 12px;
            }
        """)
        self.user_card_frame.setVisible(False)
        user_lay = QVBoxLayout(self.user_card_frame)
        user_lay.setContentsMargins(28, 24, 28, 24)
        user_lay.setSpacing(16)

        info_row = QHBoxLayout()
        info_row.setSpacing(20)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(80, 80)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            background-color: #2A2C45;
            border-radius: 40px;
            font-size: 28px;
            color: #7B7F9E;
        """)
        self.avatar_label.setText("U")
        info_row.addWidget(self.avatar_label)

        info_col = QVBoxLayout()
        info_col.setSpacing(8)

        name_row = QHBoxLayout()
        name_row.setSpacing(12)
        self.username_label = QLabel("")
        self.username_label.setObjectName("title_label")
        self.username_label.setMinimumWidth(60)
        name_row.addWidget(self.username_label)

        self.level_badge = QLabel("")
        self.level_badge.setAlignment(Qt.AlignCenter)
        self.level_badge.setStyleSheet("""
            background-color: #6C5CE7;
            color: white;
            padding: 2px 10px;
            font-size: 12px;
            font-weight: bold;
            border-radius: 4px;
        """)
        name_row.addWidget(self.level_badge)
        name_row.addStretch()
        info_col.addLayout(name_row)

        self.vip_label = QLabel("")
        self.vip_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        info_col.addWidget(self.vip_label)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(16)
        self.coin_label = QLabel("")
        self.coin_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        detail_row.addWidget(self.coin_label)
        self.follower_label = QLabel("")
        self.follower_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        detail_row.addWidget(self.follower_label)
        detail_row.addStretch()
        info_col.addLayout(detail_row)

        info_row.addLayout(info_col, stretch=1)
        user_lay.addLayout(info_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.logout_btn = QPushButton("退出登录")
        self.logout_btn.setObjectName("secondary_btn")
        self.logout_btn.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setMinimumWidth(100)
        self.logout_btn.setMinimumHeight(34)
        self.logout_btn.clicked.connect(self._on_logout)
        btn_row.addWidget(self.logout_btn)
        btn_row.addStretch()
        user_lay.addLayout(btn_row)

        lay.addWidget(self.user_card_frame)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #4E5072;")
        lay.addWidget(sep1)

        login_content = QWidget()
        login_lay = QVBoxLayout(login_content)
        login_lay.setContentsMargins(0, 0, 0, 0)
        login_lay.setSpacing(22)

        qr_grp = QGroupBox("二维码登录")
        qr_grp.setStyleSheet(qr_grp.styleSheet() + "QGroupBox { padding: 20px; }")
        qr_lay = QVBoxLayout(qr_grp)
        qr_lay.setSpacing(18)

        self.qr_label = QLabel()
        self.qr_label.setFixedSize(220, 220)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumWidth(180)
        self.qr_label.setStyleSheet("""
            background-color: #2D2F4A;
            border: 2px dashed #4E5072;
            border-radius: 12px;
            color: #7B7F9E;
            font-size: 14px;
        """)
        self.qr_label.setText("正在获取\n二维码...")
        qr_lay.addWidget(self.qr_label, alignment=Qt.AlignCenter)

        self.qr_status = QLabel("")
        self.qr_status.setObjectName("subtitle_label")
        self.qr_status.setAlignment(Qt.AlignCenter)
        self.qr_status.setWordWrap(True)
        qr_lay.addWidget(self.qr_status)

        self.qr_btn = QPushButton("获取二维码")
        self.qr_btn.setObjectName("primary_btn")
        self.qr_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        self.qr_btn.setCursor(Qt.PointingHandCursor)
        self.qr_btn.setMinimumWidth(140)
        self.qr_btn.setMinimumHeight(38)
        self.qr_btn.clicked.connect(self._on_get_qr)
        qr_lay.addWidget(self.qr_btn, alignment=Qt.AlignCenter)

        login_lay.addWidget(qr_grp)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #4E5072;")
        login_lay.addWidget(sep2)

        sess_grp = QGroupBox("SESSDATA 登录")
        sess_grp.setStyleSheet(sess_grp.styleSheet() + "QGroupBox { padding: 20px; }")
        sess_lay = QVBoxLayout(sess_grp)
        sess_lay.setSpacing(20)

        hint = QLabel("从浏览器 Cookie 中获取B站登录凭证 (F12 -> Application -> Cookies)")
        hint.setObjectName("subtitle_label")
        hint.setWordWrap(True)
        sess_lay.addWidget(hint)

        form = QVBoxLayout()
        form.setSpacing(16)

        row1 = QHBoxLayout()
        row1.setSpacing(16)
        lbl1 = QLabel("SESSDATA:")
        lbl1.setMinimumWidth(100)
        lbl1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sess_input = QLineEdit()
        self.sess_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.sess_input.setPlaceholderText("输入 SESSDATA 值...")
        self.sess_input.setMinimumHeight(40)
        self.sess_input.setMinimumWidth(200)
        row1.addWidget(lbl1)
        row1.addWidget(self.sess_input, stretch=1)
        form.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(16)
        lbl2 = QLabel("bili_jct:")
        lbl2.setMinimumWidth(100)
        lbl2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.jct_input = QLineEdit()
        self.jct_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.jct_input.setPlaceholderText("输入 bili_jct 值（可选）")
        self.jct_input.setMinimumHeight(40)
        self.jct_input.setMinimumWidth(200)
        row2.addWidget(lbl2)
        row2.addWidget(self.jct_input, stretch=1)
        form.addLayout(row2)

        sess_lay.addLayout(form)

        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        self.sess_btn = QPushButton("登 录")
        self.sess_btn.setObjectName("primary_btn")
        self.sess_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        self.sess_btn.setCursor(Qt.PointingHandCursor)
        self.sess_btn.setMinimumWidth(120)
        self.sess_btn.setMinimumHeight(38)
        self.sess_btn.clicked.connect(self._on_sess_login)
        btn_row2.addWidget(self.sess_btn)
        btn_row2.addStretch()
        sess_lay.addLayout(btn_row2)

        self.sess_status = QLabel("")
        self.sess_status.setAlignment(Qt.AlignCenter)
        self.sess_status.setWordWrap(True)
        sess_lay.addWidget(self.sess_status)

        login_lay.addWidget(sess_grp)
        self.login_content_widget = login_content
        lay.addWidget(self.login_content_widget)

        lay.addStretch(1)

        self.login_status = QLabel("")
        self.login_status.setObjectName("subtitle_label")
        lay.addWidget(self.login_status)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        creds = get_login_credentials()
        if creds.get("sessdata") and not self._logged_in:
            self._auto_login(creds)
        elif not self._logged_in and not self._qr_worker:
            self._on_get_qr()

    def _auto_login(self, creds):
        self.api.set_credentials(creds["sessdata"], creds.get("bili_jct", ""))
        self.sess_btn.setEnabled(False)
        self.sess_status.setText("正在恢复登录状态...")
        self.sess_status.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
        self.main_window.update_user_info("验证中...")

        self._verify_worker = LoginVerifyWorker(self.api)
        self._verify_worker.verify_result.connect(self._on_auto_verify_result)
        self._verify_worker.start()

    def _on_auto_verify_result(self, success, message):
        self.sess_btn.setEnabled(True)
        if success:
            save_login_credentials(
                self.api.sessdata,
                "",
                self.api.user_info,
            )
            self._show_user_card()
        else:
            clear_login_credentials()
            self.sess_status.setText("登录已过期，请重新登录")
            self.sess_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
            self.main_window.update_user_info("未登录")

    def _show_user_card(self):
        self._logged_in = True
        self.login_content_widget.hide()
        self.user_card_frame.show()

        info = self.api.user_info or {}
        username = info.get("uname", "未知用户")
        level = info.get("level", 0)
        vip_type = info.get("vip_type", 0)
        vip_status = info.get("vip_status", 0)
        vip_label_text = info.get("vip_label", "")
        coin = info.get("coin", 0)
        sex = info.get("sex", "")

        self.username_label.setText(username)
        self.level_badge.setText(f"LV{level}")

        if vip_type == 1 or vip_type == 2:
            if vip_status == 1:
                vip_color = "#FB7299"
                vip_text = f"大会员 ({vip_label_text})" if vip_label_text else "大会员"
            else:
                vip_color = "#A0AAB5"
                vip_text = f"大会员 (已过期)" if vip_label_text else "大会员 (已过期)"
        else:
            vip_color = "#A0AAB5"
            vip_text = "普通用户"

        sex_icon = ""
        if sex == "男":
            sex_icon = "♂ "
        elif sex == "女":
            sex_icon = "♀ "

        self.vip_label.setText(f"{sex_icon}{vip_text}")
        self.vip_label.setStyleSheet(f"color: {vip_color}; font-size: 13px; background: transparent;")
        self.coin_label.setText(f"硬币: {coin}")

        face_url = info.get("face", "")
        if face_url:
            self._avatar_loader = AvatarLoader(face_url)
            self._avatar_loader.avatar_loaded.connect(self._on_avatar_loaded)
            self._avatar_loader.start()

        stat = self.api.get_user_stat()
        if stat:
            self.follower_label.setText(f"粉丝: {stat.get('follower', 0)}")

        self.main_window.update_user_info(username)
        self.main_window.api = self.api

        self.login_success.emit({
            "user_info": info,
            "sessdata": self.api.sessdata,
        })

    def _on_avatar_loaded(self, pixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.avatar_label.setPixmap(scaled)
            self.avatar_label.setStyleSheet("""
                background-color: transparent;
                border-radius: 40px;
                border: 2px solid #4E5072;
            """)

    def _on_logout(self):
        clear_login_credentials()
        self._logged_in = False
        self.user_card_frame.hide()
        self.login_content_widget.show()
        self.avatar_label.setText("U")
        self.avatar_label.setPixmap(QPixmap())
        self.avatar_label.setStyleSheet("""
            background-color: #2A2C45;
            border-radius: 40px;
            font-size: 28px;
            color: #7B7F9E;
        """)
        self.sess_input.clear()
        self.jct_input.clear()
        self.sess_status.clear()
        self.login_status.clear()
        self.api = BilibiliMangaAPI()
        self.main_window.update_user_info("未登录")
        self.main_window.api = None
        self.logout_signal.emit()

    def _on_get_qr(self):
        self.qr_btn.setEnabled(False)
        self.qr_label.setText("正在获取\n二维码...")
        self.qr_label.setStyleSheet("""
            background-color: #2D2F4A;
            border: 2px dashed #4E5072;
            border-radius: 12px;
            color: #7B7F9E;
            font-size: 14px;
        """)
        self.qr_status.setText("")

        if self._qr_check_worker:
            self._qr_check_worker.stop()
            self._qr_check_worker = None

        self._qr_worker = QRCodeWorker(self.api)
        self._qr_worker.qr_ready.connect(self._on_qr_ready)
        self._qr_worker.error.connect(self._on_qr_error)
        self._qr_worker.start()

    def _on_qr_ready(self, data):
        self._qrcode_key = data.get("qrcode_key", "")
        qrcode_url = data.get("url", "")

        if qrcode_url:
            try:
                import qrcode
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=8,
                    border=2,
                )
                qr.add_data(qrcode_url)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                from io import BytesIO
                buf = BytesIO()
                img.save(buf, format='PNG')
                img_data = buf.getvalue()

                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                scaled_pixmap = pixmap.scaled(210, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.qr_label.setPixmap(scaled_pixmap)
            except ImportError:
                self.qr_label.setText("二维码已生成\n请使用B站APP扫描")
            except Exception as e:
                self.qr_label.setText(f"二维码生成失败\n{str(e)[:30]}")
        else:
            self.qr_label.setText("获取二维码URL失败")

        self.qr_status.setText("请使用B站APP扫描二维码")
        self.qr_status.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
        self.qr_btn.setEnabled(True)
        self.qr_btn.setText("刷新二维码")

        self._start_qr_polling()

    def _on_qr_error(self, msg):
        self.qr_label.setText(f"获取失败\n{msg}")
        self.qr_status.setText(msg)
        self.qr_status.setStyleSheet(f"color: {COLOR_ERROR};")
        self.qr_btn.setEnabled(True)

    def _start_qr_polling(self):
        if not self._qrcode_key:
            return

        self._qr_check_worker = QRCheckWorker(self.api, self._qrcode_key)
        self._qr_check_worker.status_update.connect(self._on_qr_status)
        self._qr_check_worker.finished.connect(self._on_qr_finished)
        self._qr_check_worker.start()

    def _on_qr_status(self, status_data):
        status = status_data.get("status", "")
        message = status_data.get("message", "")

        if status == "waiting":
            self.qr_status.setText(message)
            self.qr_status.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        elif status == "scanned":
            self.qr_status.setText(message)
            self.qr_status.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold; background: transparent;")
        elif status == "expired":
            self.qr_status.setText(message)
            self.qr_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
            self.qr_label.setText("二维码已过期\n请重新获取")
            self.qr_label.setStyleSheet("""
                background-color: rgba(255, 107, 107, 0.08);
                border: 2px dashed #FF6B6B;
                border-radius: 12px;
                color: #FF6B6B;
                font-size: 14px;
            """)
            if self._qr_check_worker:
                self._qr_check_worker.stop()
        elif status == "success":
            sessdata = status_data.get("sessdata", "")
            bili_jct = status_data.get("bili_jct", "")

            if sessdata:
                self.api.set_credentials(sessdata, bili_jct)
                verify_ok = self.api.verify_login()
                if verify_ok:
                    save_login_credentials(sessdata, bili_jct, self.api.user_info)
                    self._show_user_card()
                else:
                    self.qr_status.setText("登录验证失败，请重试")
                    self.qr_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
            else:
                self.qr_status.setText("获取登录凭证失败，请重试")
                self.qr_status.setStyleSheet(f"color: {COLOR_ERROR};")

            if self._qr_check_worker:
                self._qr_check_worker.stop()
        elif status == "error":
            self.qr_status.setText(message)
            self.qr_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
            if self._qr_check_worker:
                self._qr_check_worker.stop()

    def _on_qr_finished(self):
        pass

    def _on_sess_login(self):
        sessdata = self.sess_input.text().strip()
        bili_jct = self.jct_input.text().strip()

        if not sessdata:
            self.sess_status.setText("请输入 SESSDATA")
            self.sess_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
            return

        self.sess_btn.setEnabled(False)
        self.sess_status.setText("验证中...")
        self.sess_status.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")

        self.api.set_credentials(sessdata, bili_jct)
        self._verify_worker = LoginVerifyWorker(self.api)
        self._verify_worker.verify_result.connect(self._on_verify_result)
        self._verify_worker.start()

    def _on_verify_result(self, success, message):
        self.sess_btn.setEnabled(True)
        if success:
            save_login_credentials(
                self.api.sessdata,
                self.jct_input.text().strip(),
                self.api.user_info,
            )
            self.sess_status.setText(message)
            self.sess_status.setStyleSheet(f"color: {COLOR_SUCCESS};")
            self._show_user_card()
        else:
            self.sess_status.setText(message)
            self.sess_status.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
