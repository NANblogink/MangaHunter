from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QProgressBar,
    QScrollArea, QFrame, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from ui.styles import COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_WARNING_DARK, COLOR_ACCENT
from utils.logger import log


class CheckinWorker(QThread):
    result = pyqtSignal(dict)

    def __init__(self, api):
        super().__init__()
        self.api = api

    def run(self):
        res = self.api.checkin()
        self.result.emit(res or {"success": False, "message": "签到请求失败"})


class CheckinStatusWorker(QThread):
    status_ready = pyqtSignal(dict)

    def __init__(self, api):
        super().__init__()
        self.api = api

    def run(self):
        status = self.api.get_checkin_status()
        self.status_ready.emit(status or {})


class TaskListWorker(QThread):
    tasks_ready = pyqtSignal(dict)

    def __init__(self, api, shared_today=False):
        super().__init__()
        self.api = api
        self.shared_today = shared_today

    def run(self):
        result = self.api.get_task_list(self.shared_today)
        self.tasks_ready.emit(result or {})


class ShareWorker(QThread):
    result = pyqtSignal(dict)

    def __init__(self, api):
        super().__init__()
        self.api = api

    def run(self):
        res = self.api.share_manga()
        self.result.emit(res or {"success": False, "message": "分享请求失败"})


class DoTaskWorker(QThread):
    result = pyqtSignal(dict)

    def __init__(self, api, task_type, season_id=""):
        super().__init__()
        self.api = api
        self.task_type = task_type
        self.season_id = season_id

    def run(self):
        res = self.api.do_task(self.task_type, self.season_id)
        self.result.emit(res or {"success": False, "message": "任务执行失败"})


class CheckinPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._checkin_status = {}
        self._season_id = ""
        self._shared_today = False
        self._workers = []
        self._init_ui()

    @property
    def api(self):
        return getattr(self.main_window, 'api', None)

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container.setMinimumWidth(900)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(22)

        title = QLabel("签到与任务")
        title.setObjectName("title_label")
        layout.addWidget(title)

        info_group = QGroupBox("签到信息")
        info_group.setStyleSheet(info_group.styleSheet() + "QGroupBox { padding: 20px; }")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(16)

        info_items = [
            ("今日状态", "checkin_today", "--"),
            ("连续签到", "checkin_streak", "--"),
            ("累计签到", "checkin_total", "--"),
            ("当前积分", "checkin_point", "--"),
        ]
        self._info_labels = {}
        for i, (label_text, key, default) in enumerate(info_items):
            row, col = i // 2, (i % 2) * 2
            lbl = QLabel(label_text + ":")
            lbl.setObjectName("subtitle_label")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            info_layout.addWidget(lbl, row, col)

            val = QLabel(default)
            val.setObjectName("card_title")
            val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            info_layout.addWidget(val, row, col + 1)
            self._info_labels[key] = val

        layout.addWidget(info_group)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #4E5072;")
        layout.addWidget(sep1)

        checkin_group = QGroupBox("每日签到")
        checkin_group.setStyleSheet(checkin_group.styleSheet() + "QGroupBox { padding: 20px; }")
        checkin_layout = QVBoxLayout(checkin_group)
        checkin_layout.setSpacing(18)

        week_layout = QHBoxLayout()
        week_layout.setSpacing(10)
        self.day_labels = []
        self.day_point_labels = []
        day_points = [10, 20, 20, 10, 10, 10, 30]
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i in range(7):
            day_frame = QFrame()
            day_frame.setMinimumWidth(60)
            day_frame.setStyleSheet(
                "QFrame { background-color: #2A2C45; border: 1px solid #4E5072; border-radius: 8px; }"
            )
            day_frame_layout = QVBoxLayout(day_frame)
            day_frame_layout.setContentsMargins(10, 12, 10, 12)
            day_frame_layout.setSpacing(8)

            name_label = QLabel(day_names[i])
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setObjectName("subtitle_label")
            day_frame_layout.addWidget(name_label)

            point_label = QLabel("+{}".format(day_points[i]))
            point_label.setAlignment(Qt.AlignCenter)
            point_label.setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_ACCENT))
            day_frame_layout.addWidget(point_label)
            self.day_point_labels.append(point_label)

            check_icon = QLabel("")
            check_icon.setAlignment(Qt.AlignCenter)
            check_icon.setFixedHeight(16)
            day_frame_layout.addWidget(check_icon)

            self.day_labels.append(day_frame)
            week_layout.addWidget(day_frame, stretch=1)

        checkin_layout.addLayout(week_layout)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.checkin_btn = QPushButton("立即签到")
        self.checkin_btn.setObjectName("primary_btn")
        self.checkin_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        self.checkin_btn.setCursor(Qt.PointingHandCursor)
        self.checkin_btn.setMinimumWidth(140)
        self.checkin_btn.setMinimumHeight(42)
        self.checkin_btn.clicked.connect(self._on_checkin)
        btn_row.addWidget(self.checkin_btn)
        btn_row.addStretch()
        checkin_layout.addLayout(btn_row)

        self.checkin_result_label = QLabel("")
        self.checkin_result_label.setAlignment(Qt.AlignCenter)
        self.checkin_result_label.setWordWrap(True)
        checkin_layout.addWidget(self.checkin_result_label)

        layout.addWidget(checkin_group)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #4E5072;")
        layout.addWidget(sep2)

        share_group = QGroupBox("分享漫画 (+5积分/天)")
        share_group.setStyleSheet(share_group.styleSheet() + "QGroupBox { padding: 20px; }")
        share_layout = QVBoxLayout(share_group)
        share_layout.setSpacing(16)

        share_top = QHBoxLayout()
        share_top.setSpacing(14)

        self.share_status_label = QLabel("今日: 未分享")
        self.share_status_label.setObjectName("subtitle_label")
        share_top.addWidget(self.share_status_label)

        share_top.addStretch()

        self.share_btn = QPushButton("分 享")
        self.share_btn.setObjectName("primary_btn")
        self.share_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        self.share_btn.setCursor(Qt.PointingHandCursor)
        self.share_btn.setMinimumWidth(90)
        self.share_btn.setMinimumHeight(36)
        self.share_btn.clicked.connect(self._on_share)
        share_top.addWidget(self.share_btn)

        share_layout.addLayout(share_top)

        self.share_result_label = QLabel("")
        self.share_result_label.setWordWrap(True)
        share_layout.addWidget(self.share_result_label)

        layout.addWidget(share_group)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setFixedHeight(1)
        sep3.setStyleSheet("background-color: #4E5072;")
        layout.addWidget(sep3)

        season_group = QGroupBox("赛季任务")
        season_group.setStyleSheet(season_group.styleSheet() + "QGroupBox { padding: 20px; }")
        season_layout = QVBoxLayout(season_group)
        season_layout.setSpacing(16)

        self.season_title_label = QLabel("当前赛季: --")
        self.season_title_label.setObjectName("card_title")
        season_layout.addWidget(self.season_title_label)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["任务", "积分", "状态", "操作"])
        header = self.task_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setMinimumHeight(220)
        season_layout.addWidget(self.task_table)

        load_tasks_btn = QPushButton("加载任务列表")
        load_tasks_btn.setObjectName("secondary_btn")
        load_tasks_btn.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
        load_tasks_btn.setCursor(Qt.PointingHandCursor)
        load_tasks_btn.clicked.connect(self._load_tasks)
        season_layout.addWidget(load_tasks_btn)

        layout.addWidget(season_group, stretch=1)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        self._load_checkin_status()

    def _start_worker(self, worker):
        self._workers.append(worker)
        worker.finished = lambda: self._cleanup_worker(worker)
        worker.start()

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    def _load_checkin_status(self):
        if not self.api or not self.api.sessdata:
            self._info_labels["checkin_today"].setText("未登录")
            self._info_labels["checkin_today"].setStyleSheet("color: {}; background: transparent;".format(COLOR_ERROR))
            return

        worker = CheckinStatusWorker(self.api)
        worker.status_ready.connect(self._on_checkin_status)
        self._start_worker(worker)

    def _on_checkin_status(self, status):
        self._checkin_status = status
        today_checked = status.get("today_checked", False)
        streak = status.get("streak", 0)
        total_days = status.get("total_days", 0)
        points = status.get("points", [])

        if today_checked:
            self._info_labels["checkin_today"].setText("已签到")
            self._info_labels["checkin_today"].setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
            self.checkin_btn.setText("已签到")
            self.checkin_btn.setEnabled(False)
        else:
            self._info_labels["checkin_today"].setText("未签到")
            self._info_labels["checkin_today"].setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_WARNING))

        self._info_labels["checkin_streak"].setText("{} 天".format(streak))
        self._info_labels["checkin_total"].setText("{} 天".format(total_days))
        self._info_labels["checkin_point"].setText("--")

        if points and self.day_point_labels:
            for i in range(min(len(points), 7)):
                self.day_point_labels[i].setText("+{}".format(points[i]))

        if streak > 0 and self.day_labels:
            for i in range(min(streak, 7)):
                self.day_labels[i].setStyleSheet(
                    "QFrame { background-color: rgba(0, 210, 160, 0.10); border: 1px solid #00D2A0; border-radius: 8px; }"
                )
                if i < len(self.day_point_labels):
                    self.day_point_labels[i].setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
                children = self.day_labels[i].children()
                for child in children:
                    if isinstance(child, QLabel) and child.text() == "":
                        child.setText("V")
                        child.setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))

        log.info("签到状态:今日%s, 连续%d天, 总计%d天",
                 "已签" if today_checked else "未签", streak, total_days)

        self._check_share_status()

    def _on_checkin(self):
        if not self.api or not self.api.sessdata:
            self.checkin_result_label.setText("请先登录")
            self.checkin_result_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_ERROR))
            return

        self.checkin_btn.setEnabled(False)
        self.checkin_result_label.setText("签到中...")
        self.checkin_result_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_TEXT_SECONDARY))

        worker = CheckinWorker(self.api)
        worker.result.connect(self._on_checkin_result)
        self._start_worker(worker)

    def _on_checkin_result(self, result):
        success = result.get("success", False)
        message = result.get("message", "")

        if success:
            points = self._checkin_status.get("points", [])
            streak = self._checkin_status.get("streak", 0)
            today_point = 0
            if points and streak < len(points):
                today_point = points[streak]

            self.checkin_result_label.setText(message + (" (+{}积分)".format(today_point) if today_point > 0 else ""))
            self.checkin_result_label.setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
            self._info_labels["checkin_today"].setText("已签到")
            self._info_labels["checkin_today"].setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
            self.checkin_btn.setText("已签到")
            self.checkin_btn.setEnabled(False)

            new_streak = streak + 1
            self._info_labels["checkin_streak"].setText("{} 天".format(new_streak))
            total = self._checkin_status.get("total_days", 0) + 1
            self._info_labels["checkin_total"].setText("{} 天".format(total))

            if new_streak <= 7 and self.day_labels:
                idx = new_streak - 1
                self.day_labels[idx].setStyleSheet(
                    "QFrame { background-color: rgba(0, 210, 160, 0.10); border: 1px solid #00D2A0; border-radius: 8px; }"
                )
                if idx < len(self.day_point_labels):
                    self.day_point_labels[idx].setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
                children = self.day_labels[idx].children()
                for child in children:
                    if isinstance(child, QLabel) and child.text() == "":
                        child.setText("V")
                        child.setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))

            log.info("签到成功: %s", message)
            self._load_tasks()
        else:
            self.checkin_result_label.setText(message)
            self.checkin_result_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_ERROR))
            self.checkin_btn.setEnabled(True)
            log.warning("签到失败: %s", message)

    def _check_share_status(self):
        if not self.api or not self.api.sessdata:
            return
        worker = ShareWorker(self.api)
        worker.result.connect(self._on_share_check_result)
        self._start_worker(worker)

    def _on_share_check_result(self, result):
        success = result.get("success", False)
        message = result.get("message", "")
        if success and "已分享" in message:
            self._shared_today = True
            self.share_status_label.setText("今日: 已分享")
            self.share_status_label.setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
            self.share_btn.setText("已分享")
            self.share_btn.setEnabled(False)
            self._load_tasks()

    def _on_share(self):
        if not self.api or not self.api.sessdata:
            self.share_result_label.setText("请先登录")
            self.share_result_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_ERROR))
            return

        self.share_btn.setEnabled(False)
        self.share_result_label.setText("分享中...")

        worker = ShareWorker(self.api)
        worker.result.connect(self._on_share_result)
        self._start_worker(worker)

    def _on_share_result(self, result):
        success = result.get("success", False)
        message = result.get("message", "")
        point = result.get("point", 0)

        self.share_btn.setEnabled(True)
        self.share_result_label.setText(message + (" (+{}积分)".format(point) if point > 0 else ""))

        if success:
            self.share_result_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_SUCCESS))
            self.share_status_label.setText("今日: 已分享")
            self.share_status_label.setStyleSheet("color: {}; font-weight: bold; background: transparent;".format(COLOR_SUCCESS))
            self.share_btn.setText("已分享")
            self.share_btn.setEnabled(False)
            self._shared_today = True
            log.info("分享成功: +%d积分", point)
            self._load_tasks()
        else:
            self.share_result_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_ERROR))
            log.warning("分享失败: %s", message)

    def _load_tasks(self):
        if not self.api or not self.api.sessdata:
            self.task_table.setRowCount(0)
            return

        self.task_table.setRowCount(0)
        worker = TaskListWorker(self.api, self._shared_today)
        worker.tasks_ready.connect(self._on_tasks_ready)
        self._start_worker(worker)

    def _on_tasks_ready(self, result):
        tasks = result.get("tasks", [])
        if not tasks:
            return

        season_title = result.get("season_title", "")
        season_id = result.get("season_id", "")
        remain_amount = result.get("remain_amount", 0)
        if season_id:
            self._season_id = season_id
        if season_title:
            self.season_title_label.setText("当前赛季: {} (积分: {})".format(season_title, remain_amount))
        if remain_amount > 0:
            self._info_labels["checkin_point"].setText(str(remain_amount))

        self.task_table.setRowCount(len(tasks))
        for i, task in enumerate(tasks):
            name = task.get("name", "")
            if not name:
                task_type = task.get("type", 0)
                duration = task.get("duration", 0)
                if duration > 0:
                    name = "阅读{}分钟".format(duration)
                else:
                    type_names = {
                        18: "阅读任务", 19: "每日猜拳", 20: "阅读任务",
                        22: "分享漫画", 1: "打开通知", 2: "设置偏好",
                    }
                    name = type_names.get(task_type, "任务{}".format(task_type))
            name_item = QTableWidgetItem(name)
            self.task_table.setItem(i, 0, name_item)

            points_item = QTableWidgetItem("+{}".format(task.get("point", 0)))
            points_item.setTextAlignment(Qt.AlignCenter)
            points_item.setForeground(QColor(COLOR_ACCENT))
            self.task_table.setItem(i, 1, points_item)

            status = task.get("status", 0)
            if status == 2:
                status_text = "已完成"
                status_color = COLOR_SUCCESS
            elif status == 1:
                status_text = "待领取"
                status_color = COLOR_WARNING
            else:
                status_text = "未完成"
                status_color = COLOR_TEXT_SECONDARY
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            self.task_table.setItem(i, 2, status_item)

            if status == 2:
                done_label = QLabel("已完成")
                done_label.setAlignment(Qt.AlignCenter)
                done_label.setStyleSheet("color: {}; background: transparent;".format(COLOR_SUCCESS))
                self.task_table.setCellWidget(i, 3, done_label)
            elif status == 1:
                claim_btn = QPushButton("领取")
                claim_btn.setObjectName("primary_btn")
                claim_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
                claim_btn.setCursor(Qt.PointingHandCursor)
                claim_btn.setMinimumHeight(30)
                claim_btn.clicked.connect(lambda checked, t=task: self._do_task(t))
                self.task_table.setCellWidget(i, 3, claim_btn)
            else:
                action_btn = QPushButton("前往")
                action_btn.setObjectName("secondary_btn")
                action_btn.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
                action_btn.setCursor(Qt.PointingHandCursor)
                action_btn.setMinimumHeight(30)
                action_btn.clicked.connect(lambda checked, t=task: self._do_task(t))
                self.task_table.setCellWidget(i, 3, action_btn)

    def _do_task(self, task):
        if not self.api or not self.api.sessdata:
            return

        task_type = task.get("type", 0)
        if task_type == 100:
            self._on_checkin()
            return
        elif task_type == 101:
            self._on_share()
            return

        worker = DoTaskWorker(self.api, task_type, self._season_id)
        worker.result.connect(lambda r, t=task: self._on_task_done(r, t))
        self._start_worker(worker)

    def _on_task_done(self, result, task):
        success = result.get("success", False)
        message = result.get("message", "")

        if success:
            log.info("任务完成: %s", task.get("name", ""))
        else:
            log.warning("任务失败: %s - %s", task.get("name", ""), message)

        self._load_checkin_status()
        self._load_tasks()

    def refresh(self):
        self._load_checkin_status()
        self._load_tasks()

    def closeEvent(self, event):
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
        event.accept()
