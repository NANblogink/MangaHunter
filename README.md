<div align="center">

# MangaHunter · 漫画猎手

**Bilibili 漫画智能浏览 · 高效下载 · 自动签到**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## 项目简介

MangaHunter（漫画猎手）是一款基于 Python + PyQt5 构建的 Bilibili 漫画桌面客户端，提供漫画搜索浏览、章节下载、自动签到与任务管理等功能。采用深色主题 UI 设计，支持二维码与 Cookie 双模式登录，具备高 DPI 屏幕自适应能力。

---

## 核心功能

### 账号登录
- **二维码登录** — 调用 B站 Passport API 生成登录二维码，使用 B站 APP 扫码即可完成认证，自动获取并持久化 `SESSDATA` 与 `bili_jct`
- **SESSDATA 登录** — 支持手动从浏览器 Cookie 中提取登录凭证，适配高级用户需求
- **登录状态恢复** — 启动时自动验证已保存的凭证有效性，无需重复登录
- **用户信息展示** — 头像、等级、大会员状态、硬币余额、粉丝数等完整展示

### 漫画搜索与浏览
- **关键词搜索** — 基于 B站漫画 APP API 签名机制（appkey + sign），支持按关键词检索漫画
- **详情展示** — 展示漫画封面、作者、类型、简介、经典台词、连载状态、发布时间等完整信息
- **章节列表** — 获取并展示全部章节，标注锁定/付费/免费/可读状态及漫币价格
- **封面加载** — 异步加载漫画封面与详情封面，不阻塞主线程

### 漫画下载
- **批量下载** — 在搜索结果中勾选多个章节，一键加入下载队列
- **图片获取流程** — 先通过 `GetImageIndex` 获取章节图片路径列表，再通过 `ImageToken` 批量获取带时效的下载 Token，最终拼接 URL 完成图片下载
- **自动合成长图** — 下载完成后可选将同一话的所有图片纵向拼接为一张长图（基于 Pillow）
- **下载管理** — 实时进度条、文件大小统计、暂停/取消/打开文件夹操作
- **下载历史** — 自动记录下载历史，支持快速打开已下载的漫画文件夹

### 签到与任务
- **每日签到** — 调用漫画签到 API，展示连续签到天数与每周积分奖励（10/20/20/10/10/10/30）
- **分享漫画** — 每日分享获取 +5 积分
- **赛季任务** — 展示当前赛季任务列表，支持一键领取已完成任务的奖励
- **签到日历** — 可视化展示一周签到进度

### 设置
- **下载配置** — 自定义保存路径、图片格式（JPG/WebP）、并发下载数
- **自动化** — 可选启动时自动签到、自动分享漫画
- **账号管理** — 在设置页面直接配置或更新登录凭证

---

## 技术架构

### 整体架构

```
MangaHunter
├── main.py                  # 程序入口，初始化 QApplication 与高 DPI 支持
├── api/
│   ├── bilibili_manga.py    # Bilibili 漫画 API 封装层
│   └── config.py            # 配置持久化（JSON 读写）
├── ui/
│   ├── main_window.py       # 主窗口框架（无边框、侧边栏导航）
│   ├── styles.py            # 全局深色主题样式表
│   └── pages/
│       ├── login_page.py    # 登录页（二维码 + SESSDATA）
│       ├── search_page.py   # 搜索页（搜索 + 详情 + 章节选择）
│       ├── download_page.py # 下载页（任务队列 + 进度 + 历史）
│       ├── checkin_page.py  # 签到页（签到 + 分享 + 赛季任务）
│       └── settings_page.py # 设置页（账号 + 下载 + 自动化）
└── utils/
    └── logger.py            # 日志系统（控制台彩色 + 文件记录）
```

### API 签名机制

B站漫画 APP API 采用 **appkey + sign** 签名验证体系：

1. 将请求参数按 key 字典序排列，拼接为 `key1=value1&key2=value2...appsecret` 格式
2. 对拼接字符串计算 MD5 哈希值作为 `sign` 参数
3. 同时附加 `appkey` 与 `ts`（时间戳）参数

本程序使用已知的 APP Key 对（`cc861359204411b2` / `00f04d5df437e1bc5a246a2ec740c292`）完成签名，使搜索、章节列表等接口可正常调用。

### 图片下载流程

```
搜索漫画 → 获取漫画详情 → 获取章节列表
                                    ↓
                          GetImageIndex（获取图片路径列表）
                                    ↓
                          ImageToken（批量获取带时效 Token）
                                    ↓
                          拼接 URL + Token 下载图片
                                    ↓
                          可选：Pillow 纵向拼接为长图
```

### 多线程设计

所有网络请求均在 `QThread` 子线程中执行，通过 `pyqtSignal` 信号机制与主线程通信，确保 UI 始终流畅响应：

| Worker | 职责 |
|--------|------|
| `QRCodeWorker` | 获取登录二维码 |
| `QRCheckWorker` | 轮询扫码状态（1.5s 间隔） |
| `LoginVerifyWorker` | 验证登录凭证 |
| `SearchWorker` | 执行漫画搜索 |
| `ComicDetailWorker` | 获取漫画详情与章节 |
| `CoverLoader` | 异步加载封面图片 |
| `DownloadWorker` | 下载章节图片并合成长图 |
| `CheckinWorker` | 执行每日签到 |
| `ShareWorker` | 执行漫画分享 |
| `TaskListWorker` | 获取赛季任务列表 |

### UI 设计

- **深色主题** — 以 `#1A1B2E` / `#1E1F33` 为基底，`#6C5CE7` 紫色为强调色的现代暗色方案
- **无边框窗口** — 自定义标题栏，支持拖拽移动、边缘缩放、双击最大化
- **高 DPI 适配** — 自动检测屏幕 DPI 并按比例缩放窗口尺寸与字体
- **自定义控件** — 导航按钮、进度条、滚动条、复选框等全部自定义样式

---

## 快速开始

### 环境要求

- Python 3.8+
- Windows 操作系统

### 安装依赖

```bash
pip install PyQt5 requests qrcode Pillow
```

### 启动程序

```bash
python main.py
```

### 登录方式

1. **二维码登录（推荐）** — 启动后自动生成二维码，使用 B站 APP 扫码
2. **SESSDATA 登录** — 浏览器登录 B站 → F12 → Application → Cookies → 复制 `SESSDATA` 值

---

## 项目结构

```
MangaHunter/
├── main.py                  # 程序入口
├── .gitignore               # Git 忽略规则
├── README.md                # 项目说明
├── api/
│   ├── __init__.py
│   ├── bilibili_manga.py    # B站漫画 API 封装
│   └── config.py            # 配置管理
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # 主窗口
│   ├── styles.py            # 全局样式
│   └── pages/
│       ├── __init__.py
│       ├── login_page.py    # 登录页
│       ├── search_page.py   # 搜索页
│       ├── download_page.py # 下载页
│       ├── checkin_page.py  # 签到页
│       └── settings_page.py # 设置页
└── utils/
    ├── __init__.py
    └── logger.py            # 日志模块
```

---

## 依赖说明

| 依赖 | 用途 |
|------|------|
| `PyQt5` | GUI 框架，提供窗口、控件、布局、信号槽等 |
| `requests` | HTTP 请求库，用于调用 B站 API 与下载图片 |
| `qrcode` | 二维码生成库，用于生成登录二维码 |
| `Pillow` | 图像处理库，用于下载后合成长图 |

---

## 注意事项

- 本程序仅供学习交流使用，请勿用于商业用途
- B站漫画 API 可能随时变更，部分功能可能因 API 升级而暂时不可用
- 请尊重漫画版权，下载的内容仅供个人阅读
- `SESSDATA` 等登录凭证属于敏感信息，请勿泄露给他人

---

## 作者

- **寒烟似雪** — QQ: 2273962061
- **逸雨** — QQ: 3241417097

网站: [www.myblog.ink](https://www.myblog.ink)

---

<div align="center">

**MangaHunter** — 用技术，让阅读更自由。

</div>
