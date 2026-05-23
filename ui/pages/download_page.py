import os
import json
import time
import requests as req

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QFileDialog, QScrollArea, QFrame,
    QCheckBox, QMessageBox, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QPoint
from PyQt5.QtGui import QColor

from ui.styles import COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_WARNING_DARK
from utils.logger import log

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORY_PATH = os.path.join(_PROJECT_ROOT, "download_history.json")

STYLE_PRIMARY_BTN = "background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;"
STYLE_SECONDARY_BTN = "background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;"
STYLE_LINEEDIT = "background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;"
STYLE_CHECKBOX = "QCheckBox { spacing: 10px; font-size: 13px; color: #E8E9F0; background: transparent; } QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #4E5072; background-color: #2D2F4A; border-radius: 4px; } QCheckBox::indicator:hover { border-color: #6C5CE7; background-color: #2A2C45; } QCheckBox::indicator:checked { background-color: #6C5CE7; border-color: #6C5CE7; image: none; } QCheckBox::indicator:unchecked { border: 2px solid #4E5072; background-color: #2D2F4A; }"

TOAST_STYLES = {
    "info": "background-color: #252740; border-left: 4px solid #6C5CE7; border-radius: 8px; padding: 12px 20px; color: #E8E9F0; font-size: 13px;",
    "success": "background-color: #252740; border-left: 4px solid #00D2A0; border-radius: 8px; padding: 12px 20px; color: #E8E9F0; font-size: 13px;",
    "error": "background-color: #252740; border-left: 4px solid #FF6B6B; border-radius: 8px; padding: 12px 20px; color: #E8E9F0; font-size: 13px;",
}


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal(str, bool)
    size_update = pyqtSignal(str)

    def __init__(self, api, comic_id, episode_id, save_path, task_name, comic_title="", merge_long_image=True):
        super().__init__()
        self.api = api
        self.comic_id = comic_id
        self.episode_id = episode_id
        self.save_path = save_path
        self.task_name = task_name
        self.comic_title = comic_title
        self.merge_long_image = merge_long_image
        self._running = True

    def stop(self):
        self._running = False
        self.wait(2000)

    def _merge_long_image(self, chapter_dir, safe_chapter):
        try:
            from PIL import Image
        except ImportError:
            log.warning("PIL未安装，跳过长图合成")
            return

        img_files = sorted([
            f for f in os.listdir(chapter_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ])
        if not img_files:
            return

        images = []
        for f in img_files:
            if not self._running:
                return
            fp = os.path.join(chapter_dir, f)
            try:
                img = Image.open(fp)
                if img.mode == "RGBA":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)
            except Exception as e:
                log.warning("打开图片失败(合成跳过): %s - %s", f, e)

        if not images:
            return

        max_w = max(img.width for img in images)
        total_h = sum(img.height for img in images)

        result = Image.new("RGB", (max_w, total_h), (255, 255, 255))
        y = 0
        for img in images:
            if not self._running:
                return
            if img.width < max_w:
                x = (max_w - img.width) // 2
            else:
                x = 0
            result.paste(img, (x, y))
            y += img.height

        long_img_path = os.path.join(chapter_dir, f"{safe_chapter}_长图.jpg")
        result.save(long_img_path, "JPEG", quality=95)
        log.info("长图合成完成: %s (%dx%d)", long_img_path, max_w, total_h)

    def run(self):
        try:
            if not self._running:
                return

            log.info("开始下载: %s (ep_id=%s)", self.task_name, self.episode_id)
            self.status.emit("获取章节图片列表...")
            image_data = self.api.get_chapter_images(self.comic_id, self.episode_id)

            if not self._running:
                return

            if not image_data or not image_data.get("images"):
                self.status.emit("获取图片列表失败")
                self.finished_signal.emit(self.task_name, False)
                return

            images = image_data.get("images", [])
            total = len(images)

            if total == 0:
                self.status.emit("无图片")
                self.finished_signal.emit(self.task_name, False)
                return

            safe_comic = "".join(c for c in self.comic_title if c.isalnum() or c in (" ", "-", "_", "(", ")")).strip()
            safe_chapter = "".join(c for c in self.task_name if c.isalnum() or c in (" ", "-", "_", "(", ")")).strip()
            chapter_dir = os.path.join(self.save_path, safe_comic, safe_chapter)
            os.makedirs(chapter_dir, exist_ok=True)

            self.status.emit("获取图片Token...")
            token_urls = ["https://i0.hdslb.com{}".format(img.get("path", "")) for img in images]
            tokens = self.api.get_image_token_batch(token_urls, batch_size=20)

            if not self._running:
                return

            if not tokens:
                self.status.emit("获取Token失败")
                self.finished_signal.emit(self.task_name, False)
                return

            log.info("获取到%d个Token, 开始下载图片", len(tokens))
            self.status.emit("下载中 (0/{})".format(total))
            downloaded_size = 0
            success_count = 0

            for i, token_item in enumerate(tokens):
                if not self._running:
                    self.status.emit("已暂停")
                    return

                try:
                    download_url = token_item.get("url", "")
                    token = token_item.get("token", "")

                    if not download_url or not token:
                        continue

                    full_url = "{}?token={}".format(download_url, token)

                    ext = ".jpg"
                    if download_url.lower().endswith(".webp"):
                        ext = ".webp"
                    filename = "{}{}".format(str(i + 1).zfill(4), ext)
                    filepath = os.path.join(chapter_dir, filename)

                    headers = {
                        'Referer': 'https://manga.bilibili.com/',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    }

                    resp = req.get(full_url, headers=headers, timeout=30)
                    if resp.status_code == 200 and len(resp.content) > 500:
                        with open(filepath, 'wb') as f:
                            f.write(resp.content)
                        downloaded_size += len(resp.content)
                        success_count += 1
                except Exception as e:
                    log.warning("下载第%d张图片失败: %s", i + 1, e)

                progress = int((i + 1) / total * 100)
                self.progress.emit(progress)
                self.status.emit("下载中 ({}/{})".format(i + 1, total))

                size_mb = downloaded_size / (1024 * 1024)
                self.size_update.emit("{:.1f} MB".format(size_mb))

            if success_count > 0:
                final_size = downloaded_size / (1024 * 1024)
                self.size_update.emit("{:.1f} MB".format(final_size))

                if self.merge_long_image and self._running:
                    self.status.emit("合成长图中...")
                    try:
                        self._merge_long_image(chapter_dir, safe_chapter)
                    except Exception as e:
                        log.warning("合成长图失败: %s - %s", self.task_name, e)

                if not self._running:
                    return

                self.status.emit("已完成")
                log.info("下载完成: %s (%d/%d张, %.1fMB)", self.task_name, success_count, total, final_size)
                self.finished_signal.emit(self.task_name, True)
            else:
                self.status.emit("下载失败")
                log.error("下载失败: %s (0/%d张)", self.task_name, total)
                self.finished_signal.emit(self.task_name, False)

        except Exception as e:
            if self._running:
                self.status.emit("错误: {}".format(str(e)[:50]))
                log.error("下载异常: %s - %s", self.task_name, e)
                self.finished_signal.emit(self.task_name, False)


class DownloadPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._tasks = []
        self._workers = []
        self._history = []
        self._current_toast = None
        self._toast_anim = None
        self._toast_timer = None
        self._init_ui()
        self._load_history()

    @property
    def api(self):
        return getattr(self.mw, 'api', None)

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
        lay.setContentsMargins(40, 32, 40, 32)
        lay.setSpacing(22)

        lay.addWidget(self._title("下载管理"))

        sg = QGroupBox("下载设置")
        sg.setStyleSheet(sg.styleSheet() + "QGroupBox { padding: 20px; }")
        sl = QVBoxLayout(sg)
        sl.setSpacing(18)

        path_row = QHBoxLayout()
        path_row.setSpacing(12)
        path_label = QLabel("保存路径:")
        path_label.setMinimumWidth(80)
        path_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.path_input = QLineEdit()
        self.path_input.setText(os.path.join(os.path.expanduser("~"), "Downloads", "manga"))
        self.path_input.setMinimumHeight(40)
        self.path_input.setMinimumWidth(200)
        self.path_input.setStyleSheet(STYLE_LINEEDIT)
        path_row.addWidget(path_label)
        path_row.addWidget(self.path_input, stretch=1)
        browse = QPushButton("浏览")
        browse.setObjectName("secondary_btn")
        browse.setStyleSheet(STYLE_SECONDARY_BTN)
        browse.setCursor(Qt.PointingHandCursor)
        browse.setMinimumWidth(70)
        browse.setMinimumHeight(38)
        browse.clicked.connect(self._on_browse)
        path_row.addWidget(browse)
        sl.addLayout(path_row)

        fg = QGroupBox("图片格式")
        fg.setStyleSheet(fg.styleSheet() + "QGroupBox { padding: 20px; }")
        fl = QHBoxLayout(fg)
        fl.setSpacing(20)
        self.jpg_cb = QCheckBox("JPG")
        self.jpg_cb.setChecked(True)
        self.jpg_cb.setStyleSheet(STYLE_CHECKBOX)
        fl.addWidget(self.jpg_cb)
        self.webp_cb = QCheckBox("WebP")
        self.webp_cb.setStyleSheet(STYLE_CHECKBOX)
        fl.addWidget(self.webp_cb)
        self.merge_cb = QCheckBox("自动合成长图")
        self.merge_cb.setChecked(True)
        self.merge_cb.setStyleSheet(STYLE_CHECKBOX)
        self.merge_cb.setToolTip("下载完成后自动将同一话的图片纵向拼接为一张长图")
        fl.addWidget(self.merge_cb)
        fl.addStretch()
        fl.addWidget(QLabel("并发数:"))
        self.concurrent = QLineEdit("3")
        self.concurrent.setMinimumWidth(50)
        self.concurrent.setMaximumWidth(80)
        self.concurrent.setAlignment(Qt.AlignCenter)
        self.concurrent.setMinimumHeight(34)
        self.concurrent.setStyleSheet(STYLE_LINEEDIT)
        fl.addWidget(self.concurrent)
        lay.addWidget(fg)

        lay.addWidget(sg)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #4E5072;")
        lay.addWidget(sep1)

        tg = QGroupBox("下载任务")
        tg.setStyleSheet(tg.styleSheet() + "QGroupBox { padding: 20px; }")
        tl = QVBoxLayout(tg)
        tl.setSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.pause_btn = QPushButton("全部暂停")
        self.pause_btn.setObjectName("secondary_btn")
        self.pause_btn.setStyleSheet(STYLE_SECONDARY_BTN)
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.setMinimumHeight(36)
        self.pause_btn.clicked.connect(self._on_pause_all)
        btn_row.addWidget(self.pause_btn)
        self.clear_btn = QPushButton("清除已完成")
        self.clear_btn.setObjectName("secondary_btn")
        self.clear_btn.setStyleSheet(STYLE_SECONDARY_BTN)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.clicked.connect(self._on_clear_done)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        self.count_label = QLabel("0 个任务")
        self.count_label.setObjectName("subtitle_label")
        btn_row.addWidget(self.count_label)
        tl.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["漫画/章节", "状态", "进度", "大小", "操作"])
        hdr = self.table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(300)
        tl.addWidget(self.table)

        lay.addWidget(tg, stretch=1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #4E5072;")
        lay.addWidget(sep2)

        hg = QGroupBox("下载历史")
        hg.setStyleSheet(hg.styleSheet() + "QGroupBox { padding: 20px; }")
        hl = QVBoxLayout(hg)
        hl.setSpacing(12)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["漫画名", "章节", "大小", "下载时间", "操作"])
        hh = self.history_table.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setMinimumHeight(200)
        self.history_table.setMaximumHeight(350)
        hl.addWidget(self.history_table)

        lay.addWidget(hg)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _title(self, text):
        l = QLabel(text)
        l.setObjectName("title_label")
        return l

    def _on_browse(self):
        p = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if p:
            self.path_input.setText(p)

    def add_task(self, comic_title="", chapter_name="", comic_id=None, episode_id=None):
        name = f"{comic_title} - {chapter_name}" if comic_title and chapter_name else (comic_title or chapter_name or "未知任务")

        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, name_item)
        si = QTableWidgetItem("准备中...")
        si.setTextAlignment(Qt.AlignCenter)
        si.setForeground(QColor(COLOR_WARNING_DARK))
        self.table.setItem(row, 1, si)
        pb = QProgressBar()
        pb.setValue(0)
        pb.setFixedHeight(24)
        pb.setMinimumWidth(140)
        self.table.setCellWidget(row, 2, pb)
        self.table.setItem(row, 3, self._center_item("-"))
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondary_btn")
        cancel_btn.setStyleSheet(STYLE_SECONDARY_BTN)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(lambda checked, r=row: self._cancel_task(r))
        self.table.setCellWidget(row, 4, cancel_btn)

        task_info = {
            "row": row,
            "name": name,
            "comic_title": comic_title,
            "chapter_name": chapter_name,
            "comic_id": comic_id,
            "episode_id": episode_id,
            "worker": None,
        }
        self._tasks.append(task_info)
        self.count_label.setText(f"{self.table.rowCount()} 个任务")

        self._show_toast(f"已添加下载任务: {name}", "info")

        if comic_id and episode_id:
            self._start_download(task_info)

    def _start_download(self, task_info):
        if not self.api:
            self._update_task_status(task_info["row"], "未登录", COLOR_ERROR)
            return

        save_path = self.path_input.text().strip()
        if not save_path:
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", "manga")

        task_info["save_path"] = save_path

        worker = DownloadWorker(
            self.api,
            task_info["comic_id"],
            task_info["episode_id"],
            save_path,
            task_info["chapter_name"],
            task_info["comic_title"],
            self.merge_cb.isChecked()
        )
        worker.progress.connect(lambda p, r=task_info["row"]: self._update_progress(r, p))
        worker.status.connect(lambda s, r=task_info["row"]: self._update_task_status(r, s, ""))
        worker.finished_signal.connect(lambda n, s, r=task_info["row"]: self._on_finished(r, n, s))
        worker.size_update.connect(lambda sz, r=task_info["row"]: self._update_size(r, sz))

        task_info["worker"] = worker
        self._workers.append(worker)
        worker.start()
        self._show_toast(f"开始下载: {task_info['name']}", "info")

    def _cancel_task(self, row):
        for task in self._tasks:
            if task["row"] == row:
                if task.get("worker"):
                    task["worker"].stop()
                self._update_task_status(row, "已取消", COLOR_ERROR)
                break

    def _update_progress(self, row, value):
        pb = self.table.cellWidget(row, 2)
        if pb:
            pb.setValue(value)

    def _update_task_status(self, row, text, color=""):
        si = self.table.item(row, 1)
        if si:
            si.setText(text)
            if color:
                si.setForeground(QColor(color))
            elif text == "下载中" or text == "已完成":
                si.setForeground(QColor(COLOR_SUCCESS))
            elif text in ("已暂停", "已取消", "下载失败"):
                si.setForeground(QColor(COLOR_ERROR))
            elif text.startswith("错误") or "失败" in text:
                si.setForeground(QColor(COLOR_ERROR))
            else:
                si.setForeground(QColor(COLOR_WARNING))

    def _update_size(self, row, size_text):
        sz = self.table.item(row, 3)
        if sz:
            sz.setText(size_text)

    def _on_finished(self, row, task_name, success):
        if row is not None:
            task = None
            for t in self._tasks:
                if t["row"] == row:
                    task = t
                    break

            if success:
                self._update_task_status(row, "已完成", COLOR_SUCCESS)
                btn = self.table.cellWidget(row, 4)
                if btn:
                    btn.setText("打开文件夹")
                    btn.setStyleSheet(STYLE_SECONDARY_BTN)
                    btn.clicked.disconnect()
                    if task:
                        btn.clicked.connect(lambda checked, t=task: self._open_folder(t))

                if task:
                    save_path = task.get("save_path", self.path_input.text().strip())
                    if not save_path:
                        save_path = os.path.join(os.path.expanduser("~"), "Downloads", "manga")
                    safe_comic = "".join(c for c in task["comic_title"] if c.isalnum() or c in (" ", "-", "_", "(", ")")).strip()
                    safe_chapter = "".join(c for c in task["chapter_name"] if c.isalnum() or c in (" ", "-", "_", "(", ")")).strip()
                    full_path = os.path.join(save_path, safe_comic, safe_chapter)
                    size_item = self.table.item(row, 3)
                    size_text = size_item.text() if size_item else "-"
                    entry = {
                        "comic_title": task["comic_title"],
                        "chapter_name": task["chapter_name"],
                        "path": full_path,
                        "time": time.strftime("%Y-%m-%d %H:%M"),
                        "size": size_text,
                    }
                    self._history.append(entry)
                    self._save_history()
                    self._add_history_row(entry)

                self._show_toast(f"下载完成: {task['name'] if task else task_name}", "success")
            else:
                self._update_task_status(row, "下载失败", COLOR_ERROR)
                self._show_toast(f"下载失败: {task['name'] if task else task_name}", "error")

    def _open_folder(self, task):
        save_path = task.get("save_path", self.path_input.text().strip())
        if not save_path:
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", "manga")
        safe_comic = "".join(c for c in task["comic_title"] if c.isalnum() or c in (" ", "-", "_", "(", ")")).strip()
        safe_chapter = "".join(c for c in task["chapter_name"] if c.isalnum() or c in (" ", "-", "_", "(", ")")).strip()
        folder_path = os.path.join(save_path, safe_comic, safe_chapter)
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            QMessageBox.information(self, "提示", f"文件夹不存在:\n{folder_path}")

    def _open_history_folder(self, path):
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.information(self, "提示", f"文件夹不存在:\n{path}")

    def _center_item(self, text):
        it = QTableWidgetItem(text)
        it.setTextAlignment(Qt.AlignCenter)
        return it

    def _on_pause_all(self):
        for task in self._tasks:
            if task.get("worker"):
                task["worker"].stop()
            row = task["row"]
            si = self.table.item(row, 1)
            if si and si.text() == "下载中":
                self._update_task_status(row, "已暂停", COLOR_WARNING)

    def _on_clear_done(self):
        rm = []
        for i in range(self.table.rowCount()):
            si = self.table.item(i, 1)
            if si and si.text() in ("已完成", "已取消", "下载失败"):
                rm.append(i)
        for r in reversed(rm):
            self.table.removeRow(r)
        self.count_label.setText(f"{self.table.rowCount()} 个任务")

    def _save_history(self):
        try:
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning("保存下载历史失败: %s", e)

    def _load_history(self):
        try:
            if os.path.exists(HISTORY_PATH):
                with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
                for entry in self._history:
                    self._add_history_row(entry)
        except Exception as e:
            log.warning("加载下载历史失败: %s", e)
            self._history = []

    def _add_history_row(self, entry):
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        self.history_table.setItem(row, 0, self._center_item(entry.get("comic_title", "")))
        self.history_table.setItem(row, 1, self._center_item(entry.get("chapter_name", "")))
        self.history_table.setItem(row, 2, self._center_item(entry.get("size", "-")))
        self.history_table.setItem(row, 3, self._center_item(entry.get("time", "")))
        open_btn = QPushButton("打开文件夹")
        open_btn.setObjectName("secondary_btn")
        open_btn.setStyleSheet(STYLE_SECONDARY_BTN)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setMinimumHeight(30)
        path = entry.get("path", "")
        open_btn.clicked.connect(lambda checked, p=path: self._open_history_folder(p))
        self.history_table.setCellWidget(row, 4, open_btn)

    def _show_toast(self, message, type="info"):
        if self._current_toast is not None:
            if self._toast_anim is not None:
                try:
                    self._toast_anim.finished.disconnect()
                except Exception:
                    pass
                try:
                    self._toast_anim.stop()
                except RuntimeError:
                    pass
            if self._toast_timer is not None:
                self._toast_timer.stop()
            try:
                self._current_toast.hide()
                self._current_toast.deleteLater()
            except RuntimeError:
                pass
            self._current_toast = None
            self._toast_anim = None
            self._toast_timer = None

        toast = QFrame(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        toast.setAttribute(Qt.WA_TranslucentBackground, False)
        toast.setStyleSheet(TOAST_STYLES.get(type, TOAST_STYLES["info"]))

        toast_lay = QHBoxLayout(toast)
        toast_lay.setContentsMargins(12, 10, 20, 10)
        toast_label = QLabel(message)
        toast_label.setStyleSheet("background: transparent; color: #E8E9F0; font-size: 13px; border: none;")
        toast_lay.addWidget(toast_label)

        toast.adjustSize()
        tw = toast.sizeHint().width()
        th = toast.sizeHint().height()
        parent_pos = self.mapToGlobal(QPoint(0, 0))
        pw = max(self.width(), 400)
        px = parent_pos.x() + (pw - tw) // 2
        py = parent_pos.y() + 10
        toast.move(px, py)
        toast.raise_()
        toast.show()

        self._current_toast = toast

        effect = QGraphicsOpacityEffect(toast)
        effect.setOpacity(1.0)
        toast.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(500)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self._on_toast_fade_done)
        self._toast_anim = anim

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(anim.start)
        self._toast_timer.start(2500)

    def _on_toast_fade_done(self):
        if self._current_toast is not None:
            try:
                self._current_toast.deleteLater()
            except RuntimeError:
                pass
            self._current_toast = None

    def closeEvent(self, event):
        for worker in self._workers:
            if worker.isRunning():
                worker.stop()
        event.accept()
