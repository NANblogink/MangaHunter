from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox,
    QScrollArea, QFrame, QSizePolicy,
    QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap

from ui.styles import COLOR_TEXT_SECONDARY, COLOR_ACCENT, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_WARNING_DARK


class StoppableWorker(QThread):
    _stoppable = True

    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False
        self.wait(2000)

    def run(self):
        pass


class SearchWorker(StoppableWorker):
    search_result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api, keyword):
        super().__init__()
        self.api = api
        self.keyword = keyword

    def run(self):
        try:
            result = self.api.search_manga(self.keyword)
            if not self._running:
                return
            if result:
                self.search_result.emit(result)
            else:
                self.error.emit("搜索失败")
        except Exception as e:
            if self._running:
                self.error.emit(str(e))


class ComicDetailWorker(StoppableWorker):
    detail_ready = pyqtSignal(dict)

    def __init__(self, api, comic_id):
        super().__init__()
        self.api = api
        self.comic_id = comic_id

    def run(self):
        detail = self.api.get_comic_detail_with_chapters(self.comic_id)
        if not self._running:
            return
        if detail:
            self.detail_ready.emit(detail)
        else:
            detail2 = self.api.get_manga_detail(self.comic_id)
            if not self._running:
                return
            if detail2:
                self.detail_ready.emit(detail2)
            elif self._running:
                self.detail_ready.emit(None)


class CoverLoader(StoppableWorker):
    cover_loaded = pyqtSignal(object)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            import requests as req
            resp = req.get(self.url, timeout=8)
            if not self._running:
                return
            if resp.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(resp.content)
                if not pixmap.isNull() and self._running:
                    self.cover_loaded.emit(pixmap)
                    return
            if self._running:
                self.cover_loaded.emit(None)
        except Exception:
            if self._running:
                self.cover_loaded.emit(None)


class MangaCard(QFrame):
    clicked = None

    def __init__(self, data, mw, parent=None):
        super().__init__(parent)
        self.data = data
        self.mw = mw
        self._cover_loader = None
        self.setObjectName("manga_card")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            QFrame#manga_card {
                background-color: #252740;
                border: 1px solid #4E5072;
                border-radius: 10px;
            }
            QFrame#manga_card:hover {
                background-color: #2A2C45;
                border-color: #6C5CE7;
            }
        """)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(20)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(100, 134)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("""
            background-color: #2A2C45;
            border: 1px solid #4E5072;
            border-radius: 6px;
            color: #7B7F9E;
            font-size: 12px;
        """)
        self.cover_label.setText("加载中")
        lay.addWidget(self.cover_label)

        self.info_area = QWidget()
        ilay = QVBoxLayout(self.info_area)
        ilay.setContentsMargins(0, 0, 0, 0)
        ilay.setSpacing(6)
        ilay.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        title_row = QHBoxLayout()
        t = QLabel(data.get("title", "未知"))
        t.setObjectName("card_title")
        t.setStyleSheet("font-size:16px;font-weight:600;color:#E8E9F0;background:transparent;")
        t.setMaximumHeight(48)
        t.setWordWrap(True)
        title_row.addWidget(t, stretch=1)
        ilay.addLayout(title_row)

        self.meta_lay = QHBoxLayout()
        self.meta_lay.setSpacing(14)
        authors = data.get("author_name", [])
        if authors:
            a = QLabel(", ".join(authors[:3]))
            a.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:13px;background:transparent;")
            self.meta_lay.addWidget(a)
        styles = data.get("styles", [])
        if styles:
            sn = styles[0] if isinstance(styles[0], str) else str(styles[0])
            sl = QLabel(sn)
            sl.setStyleSheet(f"color:{COLOR_ACCENT};font-size:11px;padding:2px 8px;background:transparent;border:1px solid rgba(108,92,231,0.2);border-radius:4px;")
            sl.setMaximumWidth(100)
            self.meta_lay.addWidget(sl)
        self.meta_lay.addStretch()
        ilay.addLayout(self.meta_lay)

        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;line-height:1.4;")
        self.desc_label.setMaximumHeight(52)
        self.desc_label.setWordWrap(True)
        ilay.addWidget(self.desc_label)

        self.status_lay = QHBoxLayout()
        self.status_lay.setSpacing(16)
        is_finish = data.get("is_finish", False)
        st = "已完结" if is_finish else "连载中"
        st_color = COLOR_SUCCESS if is_finish else COLOR_ACCENT
        st_lbl = QLabel(st)
        st_lbl.setStyleSheet(f"color:{st_color};font-size:12px;font-weight:500;background:transparent;")
        self.status_lay.addWidget(st_lbl)
        
        release_time = data.get("release_time", "")
        if release_time:
            rtl = QLabel(release_time)
            rtl.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;")
            self.status_lay.addWidget(rtl)
        
        total = data.get("total", 0)
        if total:
            tl = QLabel(f"{total}话")
            tl.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;")
            self.status_lay.addWidget(tl)
        self.status_lay.addStretch()
        ilay.addLayout(self.status_lay)
        ilay.addStretch()

        lay.addWidget(self.info_area, stretch=1)
        self._load_cover()

    def _load_cover(self):
        cover_url = self.data.get("cover", "") or self.data.get("vertical_cover", "")
        if not cover_url:
            self.cover_label.setText("无封面"); return
        if not cover_url.startswith("http"):
            cover_url = ("https:" + cover_url) if cover_url.startswith("//") else ""
        if cover_url:
            self._cover_loader = CoverLoader(cover_url)
            self._cover_loader.cover_loaded.connect(self._on_cover)
            self._cover_loader.start()

    def _on_cover(self, pixmap):
        if pixmap and not pixmap.isNull():
            sc = pixmap.scaled(100, 134, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.cover_label.setPixmap(sc)
            self.cover_label.setStyleSheet("background:transparent;border:1px solid #4E5072;border-radius:6px;")

    def enrich_with_detail(self, detail):
        for i in reversed(range(self.meta_lay.count())):
            w = self.meta_lay.itemAt(i).widget()
            if w: w.deleteLater()

        authors = detail.get("author_name", [])
        if authors:
            a = QLabel(", ".join(authors[:3]))
            a.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:13px;background:transparent;")
            self.meta_lay.insertWidget(0, a)

        styles = detail.get("styles", [])
        if styles:
            sn = str(styles[0]) if styles[0] else ""
            sl = QLabel(sn)
            sl.setStyleSheet(f"color:{COLOR_ACCENT};font-size:11px;padding:2px 8px;background:transparent;border:1px solid rgba(108,92,231,0.2);border-radius:4px;")
            sl.setMaximumWidth(100)
            self.meta_lay.addWidget(sl)

        producer = detail.get("producer", "")
        if producer:
            pl = QLabel(producer)
            pl.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:11px;background:transparent;")
            self.meta_lay.addWidget(pl)
        self.meta_lay.addStretch()

        desc = detail.get("classic_lines", "") or detail.get("description", "")
        if desc:
            self.desc_label.setText((desc[:90] + "...") if len(desc) > 90 else desc)
            self.desc_label.setVisible(True)
        else:
            self.desc_label.setVisible(False)

        is_f = detail.get("is_finish", False)
        st = "已完结" if is_f else "连载中"
        st_c = COLOR_SUCCESS if is_f else COLOR_ACCENT
        
        rt = detail.get("release_time", "")
        tt = detail.get("total", 0)
        
        for i in reversed(range(self.status_lay.count())):
            w = self.status_lay.itemAt(i).widget()
            if w: w.deleteLater()
        
        stl = QLabel(st)
        stl.setStyleSheet(f"color:{st_c};font-size:12px;font-weight:500;background:transparent;")
        self.status_lay.addWidget(stl)
        if rt:
            rtl2 = QLabel(rt)
            rtl2.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;")
            self.status_lay.addWidget(rtl2)
        if tt:
            tl2 = QLabel(f"{tt}话")
            tl2.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;")
            self.status_lay.addWidget(tl2)
        self.status_lay.addStretch()

        cover = detail.get("cover", "") or detail.get("vertical_cover", "")
        if cover and (not self.cover_label.pixmap() or self.cover_label.pixmap().isNull()):
            if self._cover_loader:
                self._cover_loader.stop()
            self._cover_loader = CoverLoader(cover)
            self._cover_loader.cover_loaded.connect(self._on_cover)
            self._cover_loader.start()

        self.data.update(detail)
        self.adjustSize()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.clicked:
            self.clicked(self.data)
        super().mousePressEvent(e)

    def cleanup(self):
        if self._cover_loader:
            self._cover_loader.stop()
            self._cover_loader = None

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)


class SearchPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._search_worker = None
        self._detail_worker = None
        self._detail_cover_loader = None
        self._current_comic = None
        self._current_card = None
        self._all_cards = []
        self._init_ui()

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
        lay.setSpacing(24)

        title = QLabel("搜索漫画")
        title.setObjectName("title_label")
        lay.addWidget(title)

        search_row = QHBoxLayout()
        search_row.setSpacing(12)
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet("background-color: #2D2F4A; border: 2px solid #4E5072; padding: 6px 12px; font-size: 13px; border-radius: 8px; color: #E8E9F0; min-height: 24px;")
        self.search_input.setPlaceholderText("输入漫画名称或ID...")
        self.search_input.setMinimumHeight(42)
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, stretch=1)
        self.search_btn = QPushButton("搜 索")
        self.search_btn.setObjectName("primary_btn")
        self.search_btn.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setMinimumWidth(100)
        self.search_btn.setMinimumHeight(42)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)
        lay.addLayout(search_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #4E5072;")
        lay.addWidget(sep1)

        self.result_label = QLabel("")
        self.result_label.setObjectName("subtitle_label")
        lay.addWidget(self.result_label)

        self.results = QVBoxLayout()
        self.results.setSpacing(14)
        lay.addLayout(self.results)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #4E5072;")
        lay.addWidget(sep2)

        self.detail_grp = QGroupBox("漫画详情")
        self.detail_grp.setStyleSheet(self.detail_grp.styleSheet() + "QGroupBox { padding: 24px; }")
        self.detail_grp.setVisible(False)
        dl = QVBoxLayout(self.detail_grp)
        dl.setSpacing(20)

        meta = QHBoxLayout()
        meta.setSpacing(22)
        self.detail_cover = QLabel("封面")
        self.detail_cover.setFixedSize(120, 162)
        self.detail_cover.setStyleSheet("background:#2A2C45;border:1px solid #4E5072;border-radius:8px;")
        self.detail_cover.setAlignment(Qt.AlignCenter)
        meta.addWidget(self.detail_cover)

        info = QVBoxLayout()
        info.setSpacing(10)
        
        tr = QHBoxLayout()
        self.detail_title = QLabel()
        self.detail_title.setObjectName("title_label")
        self.detail_title.setWordWrap(True)
        tr.addWidget(self.detail_title, stretch=1)
        info.addLayout(tr)
        
        self.detail_author = QLabel()
        self.detail_author.setObjectName("subtitle_label")
        self.detail_author.setWordWrap(True)
        info.addWidget(self.detail_author)
        
        mi = QHBoxLayout()
        mi.setSpacing(16)
        self.detail_genre = QLabel()
        self.detail_genre.setObjectName("subtitle_label")
        mi.addWidget(self.detail_genre)
        self.detail_producer = QLabel()
        self.detail_producer.setObjectName("subtitle_label")
        self.detail_producer.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;")
        mi.addWidget(self.detail_producer)
        mi.addStretch()
        info.addLayout(mi)
        
        self.detail_status = QLabel()
        self.detail_status.setObjectName("subtitle_label")
        info.addWidget(self.detail_status)
        self.detail_desc = QLabel()
        self.detail_desc.setObjectName("subtitle_label")
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setMinimumHeight(72)
        info.addWidget(self.detail_desc)
        info.addStretch()
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.fav_btn = QPushButton("加入收藏")
        self.fav_btn.setObjectName("secondary_btn")
        self.fav_btn.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
        self.fav_btn.setCursor(Qt.PointingHandCursor)
        self.fav_btn.setMinimumWidth(110)
        self.fav_btn.setMinimumHeight(36)
        self.fav_btn.setEnabled(False)
        self.fav_btn.setToolTip("B站API已升级，收藏功能暂不可用")
        self.fav_btn.clicked.connect(self._on_favorite)
        btn_row.addWidget(self.fav_btn)
        info.addLayout(btn_row)
        meta.addLayout(info, stretch=1)
        dl.addLayout(meta)

        ch_title = QLabel("章节信息")
        ch_title.setObjectName("card_title")
        dl.addWidget(ch_title)

        self.chapter_info = QLabel()
        self.chapter_info.setObjectName("subtitle_label")
        self.chapter_info.setWordWrap(True)
        self.chapter_info.setStyleSheet(f"color:{COLOR_WARNING_DARK};font-size:13px;padding:16px;background:rgba(253,203,110,0.08);border:1px solid rgba(253,203,110,0.3);border-radius:8px;")
        self.chapter_info.setMinimumHeight(60)
        dl.addWidget(self.chapter_info)

        self.ch_table = QTableWidget()
        self.ch_table.setColumnCount(5)
        self.ch_table.setHorizontalHeaderLabels(["选择", "序号", "标题", "状态", "价格"])
        hdr = self.ch_table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.ch_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ch_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ch_table.verticalHeader().setVisible(False)
        self.ch_table.setMinimumHeight(200)
        dl.addWidget(self.ch_table)

        dl_btn = QHBoxLayout()
        dl_btn.setSpacing(12)
        sa = QPushButton("全选")
        sa.setObjectName("secondary_btn")
        sa.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
        sa.setCursor(Qt.PointingHandCursor)
        sa.setMinimumHeight(34)
        sa.clicked.connect(self._on_select_all)
        dl_btn.addWidget(sa)
        da = QPushButton("取消全选")
        da.setObjectName("secondary_btn")
        da.setStyleSheet("background-color: #2D2F4A; color: #6C5CE7; border: 2px solid #4E5072; padding: 6px 18px; font-size: 13px; font-weight: 500; border-radius: 8px; min-height: 24px;")
        da.setCursor(Qt.PointingHandCursor)
        da.setMinimumHeight(34)
        da.clicked.connect(self._on_deselect_all)
        dl_btn.addWidget(da)
        dl_btn.addStretch()
        db = QPushButton("下载选中")
        db.setObjectName("primary_btn")
        db.setStyleSheet("background-color: #6C5CE7; color: #FFFFFF; border: 2px solid #7D6FF0; padding: 6px 20px; font-size: 13px; font-weight: 600; letter-spacing: 1px; border-radius: 8px; min-height: 24px;")
        db.setCursor(Qt.PointingHandCursor)
        db.setMinimumHeight(34)
        db.clicked.connect(self._on_download_selected)
        dl_btn.addWidget(db)
        dl.addLayout(dl_btn)

        lay.addWidget(self.detail_grp)
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _stop_all_workers(self):
        if self._search_worker:
            self._search_worker.stop()
            self._search_worker = None
        if self._detail_worker:
            self._detail_worker.stop()
            self._detail_worker = None
        if self._detail_cover_loader:
            self._detail_cover_loader.stop()
            self._detail_cover_loader = None
        for card in self._all_cards:
            card.cleanup()
        self._all_cards.clear()

    def _on_search(self):
        kw = self.search_input.text().strip()
        if not kw:
            self.result_label.setText("请输入搜索关键词"); return
        if not self.api or not self.api.sessdata:
            self.result_label.setText("请先登录"); return

        self._stop_all_workers()
        self.search_btn.setEnabled(False)
        self.result_label.setText("搜索中...")
        self._clear_results()
        self.detail_grp.setVisible(False)

        self._search_worker = SearchWorker(self.api, kw)
        self._search_worker.search_result.connect(self._on_search_result)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_search_result(self, result):
        comics = result.get("comics", [])
        total = result.get("total", 0)
        
        for comic in comics:
            c = MangaCard(comic, self.mw)
            c.clicked = self._show_detail
            self.results.addWidget(c)
            self._all_cards.append(c)
        
        self.result_label.setText(f"共找到 {total} 个结果 (显示 {len(comics)} 个)")
        self.search_btn.setEnabled(True)

    def _on_search_error(self, msg):
        self.result_label.setText(f"搜索失败: {msg}")
        self.result_label.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent;")
        self.search_btn.setEnabled(True)

    def _clear_results(self):
        for card in self._all_cards:
            card.cleanup()
        self._all_cards.clear()
        while self.results.count():
            item = self.results.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

    def _show_detail(self, data):
        self._current_comic = data
        comic_id = data.get("id")

        self.detail_grp.setVisible(True)
        self.detail_title.setText(data.get("title", ""))
        self.detail_author.setText("作者: " + ", ".join(data.get("author_name", [])))
        
        styles = data.get("styles", [])
        self.detail_genre.setText("类型: " + ", ".join(styles) if styles else "")
        
        producer = data.get("producer", "")
        self.detail_producer.setText(f"出版: {producer}" if producer else "")
        self.detail_producer.setVisible(bool(producer))

        st = "已完结" if data.get("is_finish") else "连载中"
        release_time = data.get("release_time", "")
        total = data.get("total", 0)
        status_text = f"状态: {st}"
        if release_time:
            status_text += f" | 发布于 {release_time}"
        if total:
            status_text += f" | 共{total}话"
        self.detail_status.setText(status_text)
        
        desc = data.get("classic_lines", "") or data.get("description", "") or "暂无简介"
        self.detail_desc.setText(desc)
        self.ch_table.setRowCount(0)

        cover_url = data.get("cover", "") or data.get("vertical_cover", "")
        if cover_url:
            if self._detail_cover_loader:
                self._detail_cover_loader.stop()
            self._detail_cover_loader = CoverLoader(cover_url)
            self._detail_cover_loader.cover_loaded.connect(self._on_detail_cover)
            self._detail_cover_loader.start()

        total_chapters = data.get("total", 0) or data.get("last_ord", 0)
        if total_chapters > 0:
            self.chapter_info.setText(
                f"B站漫画API已升级，章节列表暂无法获取。\n"
                f"该漫画共有 {total_chapters} 话。如需阅读请前往 B站漫画网页版 或 B站APP。"
            )
        else:
            self.chapter_info.setText("正在加载详细信息...")

        if self.api and comic_id:
            self.result_label.setText("正在加载完整信息...")
            if self._detail_worker:
                self._detail_worker.stop()
            self._detail_worker = ComicDetailWorker(self.api, comic_id)
            self._detail_worker.detail_ready.connect(self._on_detail_ready)
            self._detail_worker.start()

        for c in self._all_cards:
            if c.data.get("id") == comic_id:
                self._current_card = c
                break

    def _on_detail_cover(self, pixmap):
        if pixmap and not pixmap.isNull():
            sc = pixmap.scaled(120, 162, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.detail_cover.setPixmap(sc)
            self.detail_cover.setStyleSheet("background:transparent;border:1px solid #4E5072;border-radius:8px;")

    def _on_detail_ready(self, detail):
        if not detail:
            return

        self.detail_title.setText(detail.get("title", ""))
        self.detail_author.setText("作者: " + ", ".join(detail.get("author_name", [])))

        styles = detail.get("styles", [])
        self.detail_genre.setText("类型: " + ", ".join(styles) if styles else "")

        producer = detail.get("producer", "")
        self.detail_producer.setText(f"出版: {producer}" if producer else "")
        self.detail_producer.setVisible(bool(producer))

        is_f = detail.get("is_finish", False)
        st = "已完结" if is_f else "连载中"
        rt = detail.get("release_time", "")
        tt = detail.get("total", 0) or detail.get("last_ord", 0)
        ss = f"状态: {st}"
        if rt:
            ss += f" | 发布于 {rt}"
        if tt:
            ss += f" | 共{tt}话"
        self.detail_status.setText(ss)

        desc = detail.get("classic_lines", "") or detail.get("evaluate", "") or detail.get("description", "") or "暂无简介"
        self.detail_desc.setText(desc)

        chapters = detail.get("chapters", [])
        total_ch = len(chapters) or detail.get("total_chapters", 0) or detail.get("total", 0) or detail.get("last_ord", 0)
        
        if chapters:
            self.chapter_info.setText(f"共 {total_ch} 话")
            self.chapter_info.setStyleSheet("")
            self._populate_chapter_table(chapters)
        elif total_ch > 0:
            self.chapter_info.setText(
                f"B站漫画API已升级，章节列表暂无法获取。\n"
                f"该漫画共有 {total_ch} 话。如需阅读请前往 B站漫画网页版 或 B站APP。"
            )
            self.ch_table.setRowCount(0)
        else:
            self.chapter_info.setText("暂无章节数据")
            self.ch_table.setRowCount(0)

        if self._current_card:
            self._current_card.enrich_with_detail(detail)

        self.result_label.setText("信息加载完成")

    def _populate_chapter_table(self, chapters):
        from PyQt5.QtWidgets import QCheckBox, QWidget, QHBoxLayout
        self.ch_table.setRowCount(len(chapters))
        for i, ch in enumerate(chapters):
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.setContentsMargins(4, 2, 4, 2)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setStyleSheet("QCheckBox { spacing: 10px; font-size: 13px; color: #E8E9F0; background: transparent; } QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #4E5072; background-color: #2D2F4A; border-radius: 4px; } QCheckBox::indicator:hover { border-color: #6C5CE7; background-color: #2A2C45; } QCheckBox::indicator:checked { background-color: #6C5CE7; border-color: #6C5CE7; image: none; } QCheckBox::indicator:unchecked { border: 2px solid #4E5072; background-color: #2D2F4A; }")
            cb.setEnabled(not ch.get("is_locked", False) and ch.get("can_view", True))
            cb_layout.addWidget(cb)
            self.ch_table.setCellWidget(i, 0, cb_widget)

            ord_item = QTableWidgetItem(str(ch.get("ord", i+1)))
            ord_item.setTextAlignment(Qt.AlignCenter)
            self.ch_table.setItem(i, 1, ord_item)

            title_item = QTableWidgetItem(ch.get("short_title") or ch.get("title", ""))
            title_item.setToolTip(ch.get("title", ""))
            self.ch_table.setItem(i, 2, title_item)

            is_locked = ch.get("is_locked", False)
            pay_mode = ch.get("pay_mode", 0)
            is_in_free = ch.get("is_in_free", False)
            
            if is_locked:
                status_text = "锁定"
                status_color = COLOR_ERROR
            elif pay_mode == 1:
                status_text = "付费"
                status_color = COLOR_WARNING
            elif is_in_free:
                status_text = "免费"
                status_color = COLOR_SUCCESS
            else:
                status_text = "可读"
                status_color = COLOR_SUCCESS
            
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            self.ch_table.setItem(i, 3, status_item)

            price = ch.get("price", 0)
            price_text = f"{price}漫币" if price > 0 else "免费"
            price_item = QTableWidgetItem(price_text)
            price_item.setTextAlignment(Qt.AlignCenter)
            self.ch_table.setItem(i, 4, price_item)

    def _on_favorite(self):
        QMessageBox.information(self, "提示",
            "B站漫画API已全面升级为新的认证体系。\n"
            "收藏功能暂时不可用，\n"
            "请前往 B站漫画网页版 进行操作。")

    def _on_select_all(self):
        for i in range(self.ch_table.rowCount()):
            w = self.ch_table.cellWidget(i, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb: cb.setChecked(True)

    def _on_deselect_all(self):
        for i in range(self.ch_table.rowCount()):
            w = self.ch_table.cellWidget(i, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb: cb.setChecked(False)

    def _on_download_selected(self):
        if not self._current_comic:
            return
        sel = []
        for i in range(self.ch_table.rowCount()):
            w = self.ch_table.cellWidget(i, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb and cb.isChecked():
                    ti = self.ch_table.item(i, 2)
                    chapters = self._current_comic.get("chapters", [])
                    chapter_data = chapters[i] if i < len(chapters) else {}
                    if ti:
                        sel.append({
                            "comic": self._current_comic,
                            "chapter": ti.text(),
                            "comic_id": self._current_comic.get("id"),
                            "episode_id": chapter_data.get("id"),
                        })
        if sel:
            dp = self.mw.pages.get("download")
            if dp:
                for item in sel:
                    dp.add_task(
                        item["comic"].get("title", ""),
                        item["chapter"],
                        item.get("comic_id"),
                        item.get("episode_id")
                    )

    def closeEvent(self, event):
        self._stop_all_workers()
        super().closeEvent(event)
