import requests
import time
import hashlib
import json
import os
import base64
import uuid
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import log


class BilibiliMangaAPI:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://manga.bilibili.com/',
            'Origin': 'https://manga.bilibili.com',
        })
        self.session.cookies.update({
            "buvid3": str(uuid.uuid4()),
            "buvid4": "infoc_{}".format(uuid.uuid4()),
        })
        self.sessdata = ""
        self.user_info = None
        self._app_key = "cc861359204411b2"
        self._app_secret = "00f04d5df437e1bc5a246a2ec740c292"
        self._executor = ThreadPoolExecutor(max_workers=3)

    def set_credentials(self, sessdata: str, bili_jct: str = ""):
        self.sessdata = sessdata
        cookies = {'SESSDATA': sessdata}
        if bili_jct:
            cookies['bili_jct'] = bili_jct
        self.session.cookies.update(cookies)
        log.info("设置登录凭证")

    def _sign(self, params: dict) -> dict:
        params['appkey'] = self._app_key
        params['ts'] = int(time.time())
        sorted_params = sorted(params.items())
        sign_str = "&".join(["{}={}".format(k, v) for k, v in sorted_params])
        sign_str += self._app_secret
        params['sign'] = hashlib.md5(sign_str.encode()).hexdigest()
        return params

    def get_qr_code(self) -> Optional[Dict]:
        try:
            url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
            resp = self.session.get(url)
            result = resp.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                log.info("获取二维码成功")
                return {
                    "url": data.get("url", ""),
                    "qrcode_key": data.get("qrcode_key", ""),
                    "qrcode_image": "",
                }
            log.warning("获取二维码失败: code=%s", result.get("code"))
            return None
        except Exception as e:
            log.error("获取二维码异常: %s", e)
            return None

    def check_qr_status(self, qrcode_key: str) -> Optional[Dict]:
        try:
            url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
            resp = self.session.get(url, params={"qrcode_key": qrcode_key})
            result = resp.json()
            data = result.get("data", {})
            code = data.get("code", -1)

            if code == 86101:
                return {"status": "waiting", "message": "等待扫码"}
            elif code == 86090:
                return {"status": "scanned", "message": "已扫码，等待确认"}
            elif code == 86038:
                return {"status": "expired", "message": "二维码已过期"}
            elif code == 0:
                sessdata = ""
                bili_jct = ""
                for cookie_part in resp.headers.get("Set-Cookie", "").split(","):
                    for part in cookie_part.split(";"):
                        part = part.strip()
                        if part.startswith("SESSDATA="):
                            sessdata = part.split("=", 1)[1]
                        elif part.startswith("bili_jct="):
                            bili_jct = part.split("=", 1)[1]
                if not sessdata:
                    for cookie in self.session.cookies:
                        if cookie.name == "SESSDATA":
                            sessdata = cookie.value
                        elif cookie.name == "bili_jct":
                            bili_jct = cookie.value
                log.info("扫码登录成功")
                return {
                    "status": "success",
                    "message": "登录成功",
                    "sessdata": sessdata,
                    "bili_jct": bili_jct,
                    "url": data.get("url", ""),
                    "refresh_token": data.get("refresh_token", ""),
                }
            return {"status": "error", "message": data.get("message", "未知错误")}
        except Exception as e:
            log.error("检查二维码状态异常: %s", e)
            return None

    def verify_login(self) -> bool:
        try:
            if not self.sessdata:
                return False
            url = "https://api.bilibili.com/x/web-interface/nav"
            resp = self.session.get(url)
            result = resp.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                if data.get("isLogin"):
                    self.user_info = {
                        "mid": data.get("mid"),
                        "uname": data.get("uname"),
                        "face": data.get("face"),
                        "vip_type": data.get("vipType"),
                        "level": data.get("level_info", {}).get("current_level"),
                        "vip_status": data.get("vipStatus", 0),
                        "vip_label": data.get("vipLabel", {}).get("text", ""),
                        "coin": data.get("money", 0),
                        "sex": data.get("sex", ""),
                        "sign": data.get("sign", ""),
                        "official_verify": data.get("official_verify", {}),
                    }
                    log.info("登录验证成功: %s", data.get("uname", ""))
                    return True
            log.warning("登录验证失败")
            return False
        except Exception as e:
            log.error("验证登录异常: %s", e)
            return False

    def get_user_stat(self) -> Optional[Dict]:
        try:
            if not self.sessdata or not self.user_info:
                return None
            mid = self.user_info.get("mid")
            url = "https://api.bilibili.com/x/relation/stat?vmid={}".format(mid)
            resp = self.session.get(url)
            result = resp.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                return {"following": data.get("following", 0), "follower": data.get("follower", 0)}
            return None
        except Exception as e:
            log.error("获取用户统计异常: %s", e)
            return None

    def search_manga(self, keyword: str, page_num: int = 1, page_size: int = 20) -> Optional[Dict]:
        try:
            url = "https://manga.bilibili.com/twirp/comic.v1.Comic/Search"
            params = {
                "keyWord": keyword, "pageNum": page_num, "pageSize": page_size,
                "styleId": -1, "areaId": -1, "isFinish": -1,
                "order": 0, "waitFreeState": -1, "platform": "web",
            }
            params = self._sign(params)
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            resp = self.session.post(url, data=json.dumps(params), headers=headers, timeout=15)
            result = json.loads(resp.text.strip())
            if result.get("code") == 0:
                comics = []
                for comic in result.get("data", {}).get("list", []):
                    title = comic.get("title", "")
                    if "<em" in title:
                        import re
                        title = re.sub(r'<[^>]+>', '', title)
                    comics.append({
                        "id": comic.get("id"), "title": title,
                        "org_title": comic.get("org_title", ""),
                        "author_name": comic.get("author_name", []),
                        "styles": comic.get("styles", []),
                        "cover": comic.get("vertical_cover", ""),
                        "horizontal_cover": comic.get("horizontal_cover", ""),
                        "square_cover": comic.get("square_cover", ""),
                        "is_finish": bool(comic.get("is_finish", 0)),
                        "allow_wait_free": comic.get("allow_wait_free", False),
                        "is_locked": False, "total": 0,
                    })
                total = result.get("data", {}).get("pageInfo", {}).get("totalNum", len(comics))
                log.info("搜索[%s]找到 %d 个结果", keyword, total)
                return {"comics": comics, "total": total, "page_num": page_num}
            log.warning("搜索[%s]失败: code=%s", keyword, result.get("code"))
            return None
        except Exception as e:
            log.error("搜索漫画异常: %s", e)
            return None

    def get_manga_detail(self, comic_id: int) -> Optional[Dict]:
        try:
            url = "https://manga.bilibili.com/twirp/comic.v1.Comic/GetComic"
            params = {"comicId": comic_id, "id": comic_id}
            params = self._sign(params)
            headers = {"Content-Type": "application/json"}
            resp = self.session.post(url, data=json.dumps(params), headers=headers, timeout=15)
            result = json.loads(resp.text.strip())
            if result.get("code") == 0:
                data = result.get("data", {})
                authors = data.get("authors", [])
                author_names = [a.get("name", "") if isinstance(a, dict) else a for a in authors] if isinstance(authors, list) else []
                styles = data.get("styles", [])
                style_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in styles] if isinstance(styles, list) else []
                log.info("获取漫画详情: %s", data.get("title", ""))
                return {
                    "id": data.get("id"), "title": data.get("title"),
                    "author_name": author_names, "styles": style_names,
                    "cover": data.get("vertical_cover", ""),
                    "horizontal_cover": data.get("horizontal_cover", ""),
                    "square_cover": data.get("square_cover", ""),
                    "description": data.get("evaluate", ""),
                    "classic_lines": data.get("classic_lines", ""),
                    "is_finish": bool(data.get("is_finish", 0)),
                    "total": data.get("total", 0), "last_ord": data.get("last_ord", 0),
                    "status": data.get("status", 0), "release_time": data.get("release_time", ""),
                    "producer": data.get("producer", ""),
                    "allow_wait_free": False, "is_locked": False,
                    "fav_count": 0, "like_count": 0,
                }
            return None
        except Exception as e:
            log.error("获取漫画详情异常: %s", e)
            return None

    def get_comic_detail_with_chapters(self, comic_id: int) -> Optional[Dict]:
        try:
            url = "https://apis.netstart.cn/bcomic/ComicDetail"
            params = {"comicId": comic_id, "device": "pc"}
            headers = {'Referer': 'https://manga.bilibili.com/', 'User-Agent': self.session.headers['User-Agent']}
            resp = self.session.get(url, params=params, headers=headers, timeout=15)
            result = json.loads(resp.text.strip())
            if result.get("code") == 0:
                data = result.get("data", {})
                authors = data.get("author_name", [])
                author_names = [a.get("name", "") if isinstance(a, dict) else a for a in authors] if isinstance(authors, list) else []
                styles = data.get("styles", [])
                style_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in styles] if isinstance(styles, list) else []
                chapters = []
                ep_list = data.get("ep_list", [])
                if isinstance(ep_list, list):
                    for ep in ep_list:
                        chapters.append({
                            "id": ep.get("id", ep.get("episodeId", "")),
                            "short_title": ep.get("shortTitle", ep.get("short_title", "")),
                            "title": ep.get("longTitle", ep.get("long_title", "")),
                            "ord": ep.get("ord", ep.get("episode", 0)),
                            "is_locked": bool(ep.get("isLocked", ep.get("is_locked", False))),
                            "pay_mode": ep.get("payMode", ep.get("pay_mode", 0)),
                            "price": ep.get("price", 0),
                            "is_in_free": bool(ep.get("isInFree", ep.get("is_in_free", False))),
                            "can_view": bool(ep.get("canView", True)),
                        })
                log.info("获取漫画详情+章节: %s (%d话)", data.get("title", ""), len(chapters))
                return {
                    "id": data.get("id"), "title": data.get("title"),
                    "author_name": author_names, "styles": style_names,
                    "cover": data.get("vertical_cover", ""),
                    "horizontal_cover": data.get("horizontal_cover", ""),
                    "square_cover": data.get("square_cover", ""),
                    "description": data.get("evaluate", ""),
                    "classic_lines": data.get("classic_lines", ""),
                    "is_finish": bool(data.get("is_finish", 0)),
                    "total": data.get("total", 0), "last_ord": data.get("last_ord", 0),
                    "status": data.get("status", 0), "release_time": data.get("release_time", ""),
                    "producer": data.get("producer", ""),
                    "allow_wait_free": bool(data.get("allow_wait_free", 0)),
                    "is_locked": bool(data.get("isLocked", data.get("is_locked", False))),
                    "fav_count": data.get("favoriteCount", data.get("fav_count", 0)),
                    "like_count": data.get("likeCount", data.get("like_count", 0)),
                    "chapters": chapters, "total_chapters": len(chapters),
                }
            return None
        except Exception as e:
            log.error("获取漫画完整详情异常: %s", e)
            return None

    def get_chapter_list(self, comic_id: int, page_num: int = 1, page_size: int = 100) -> Optional[List[Dict]]:
        try:
            url = "https://manga.bilibili.com/twirp/comic.v1.Comic/Index"
            params = {"comicId": comic_id, "ep_id": 1, "pageNum": page_num, "pageSize": page_size, "platform": "web"}
            params = self._sign(params)
            headers = {"Content-Type": "application/json"}
            resp = self.session.post(url, data=json.dumps(params), headers=headers, timeout=15)
            text = resp.text.strip()
            if not text or text[0] != "{":
                url2 = "https://manga.bilibili.com/mc-api/v2/comic/episode"
                resp2 = self.session.post(url2, json={"comicId": comic_id, "pageNum": page_num, "pageSize": page_size}, timeout=15)
                text = resp2.text.strip()
            if text and text[0] in "{[":
                result = json.loads(text)
                if result.get("code") == 0:
                    d = result.get("data", {})
                    for key in ["epList", "ep_list", "episodes", "data"]:
                        eps = d.get(key, [])
                        if isinstance(eps, list) and eps:
                            chapters = []
                            for ep in eps:
                                chapters.append({
                                    "id": ep.get("id", ep.get("episodeId", ep.get("epId", ""))),
                                    "short_title": ep.get("shortTitle", ep.get("short_title", ep.get("title", ""))),
                                    "title": ep.get("longTitle", ep.get("long_title", "")),
                                    "ord": ep.get("ord", ep.get("episode", 0)),
                                    "is_locked": bool(ep.get("isLocked", ep.get("is_locked", False))),
                                    "pay_mode": ep.get("payMode", ep.get("pay_mode", 0)),
                                    "price": ep.get("price", 0),
                                    "is_in_free": bool(ep.get("isInFree", ep.get("is_in_free", False))),
                                    "can_view": bool(ep.get("canView", True)),
                                })
                            return chapters
            return None
        except Exception as e:
            log.error("获取章节列表异常: %s", e)
            return None

    def get_chapter_images(self, comic_id: int, episode_id: int) -> Optional[Dict]:
        try:
            url = "https://apis.netstart.cn/bcomic/GetImageIndex"
            params = {"epId": episode_id, "device": "pc"}
            headers = {'Referer': 'https://manga.bilibili.com/', 'User-Agent': self.session.headers['User-Agent']}
            resp = self.session.get(url, params=params, headers=headers, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                images = [{"path": img.get("path", ""), "x": img.get("x", 0), "y": img.get("y", 0)} for img in data.get("images", [])]
                log.info("获取章节图片: ep=%d, 共%d张", episode_id, len(images))
                return {"host": data.get("host", "https://manga.hdslb.com"), "images": images, "quality": data.get("quality", "")}
            log.warning("获取章节图片失败: code=%s, msg=%s", result.get("code"), result.get("msg"))
            return None
        except Exception as e:
            log.error("获取章节图片异常: %s", e)
            return None

    def get_image_token(self, urls: List[str]) -> Optional[List[Dict]]:
        try:
            url = "https://apis.netstart.cn/bcomic/ImageToken"
            params = {"urls": json.dumps(urls)}
            headers = {'Referer': 'https://manga.bilibili.com/', 'User-Agent': self.session.headers['User-Agent']}
            resp = self.session.get(url, params=params, headers=headers, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                tokens = result.get("data", [])
                log.info("获取图片Token: %d张", len(tokens))
                return tokens
            log.warning("获取图片Token失败: code=%s", result.get("code"))
            return None
        except Exception as e:
            log.error("获取图片Token异常: %s", e)
            return None

    def get_image_token_batch(self, urls: List[str], batch_size: int = 20) -> Optional[List[Dict]]:
        all_tokens = []
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            tokens = self.get_image_token(batch)
            if tokens:
                all_tokens.extend(tokens)
            else:
                log.warning("批量Token第%d批失败", i // batch_size + 1)
            if i + batch_size < len(urls):
                time.sleep(0.2)
        return all_tokens if all_tokens else None

    def download_image(self, url: str, save_path: str) -> bool:
        try:
            headers = {'Referer': 'https://manga.bilibili.com/', 'User-Agent': self.session.headers['User-Agent']}
            resp = self.session.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                return True
            return False
        except Exception as e:
            log.error("下载图片异常: %s", e)
            return False

    def checkin(self) -> Optional[Dict]:
        try:
            if not self.sessdata:
                return {"success": False, "message": "未登录"}
            url = "https://manga.bilibili.com/twirp/activity.v1.Activity/ClockIn"
            resp = self.session.post(url, data={"platform": "android"}, timeout=15)
            result = resp.json()
            code = result.get("code")
            msg = result.get("msg", "")
            if code == 0:
                if "已签到" in msg or "已签" in msg:
                    log.info("今日已签到")
                    return {"success": True, "message": "今日已签到"}
                log.info("签到成功")
                return {"success": True, "message": "签到成功"}
            elif code == "invalid_argument" or "duplicate" in msg:
                log.info("今日已签到")
                return {"success": True, "message": "今日已签到"}
            else:
                log.warning("签到失败: %s", msg)
                return {"success": False, "message": msg or "签到失败"}
        except Exception as e:
            log.error("签到异常: %s", e)
            return {"success": False, "message": str(e)}

    def get_checkin_status(self) -> Optional[Dict]:
        try:
            if not self.sessdata:
                return None
            url = "https://manga.bilibili.com/twirp/activity.v1.Activity/GetClockInInfo"
            resp = self.session.post(url, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                points = data.get("points", [])
                status = {
                    "today_checked": data.get("status", 0) == 1,
                    "streak": data.get("day_count", 0),
                    "total_days": data.get("day_count", 0),
                    "point": 0,
                    "points": points,
                }
                log.info("签到状态: 今日%s, 连续%d天, 积分列表%s",
                         "已签" if status["today_checked"] else "未签",
                         status["streak"], points)
                return status
            return None
        except Exception as e:
            log.error("获取签到状态异常: %s", e)
            return None

    def share_manga(self, comic_id: int = 0) -> Optional[Dict]:
        try:
            if not self.sessdata:
                return {"success": False, "message": "未登录"}
            url = "https://manga.bilibili.com/twirp/activity.v1.Activity/ShareComic"
            resp = self.session.post(url, data={"platform": "android"}, timeout=15)
            result = resp.json()
            code = result.get("code")
            msg = result.get("msg", "")
            if code == 0:
                if "已分享" in msg:
                    log.info("今日已分享")
                    return {"success": True, "message": "今日已分享"}
                point = result.get("data", {}).get("point", 0)
                log.info("分享成功! +%d积分", point)
                return {"success": True, "message": "分享成功", "point": point}
            elif code == "invalid_argument":
                arg = result.get("meta", {}).get("argument", "")
                if arg == "platform":
                    log.warning("分享失败: 缺少platform参数")
                    return {"success": False, "message": "缺少platform参数"}
                log.warning("分享失败: %s", msg)
                return {"success": False, "message": msg or "参数错误"}
            elif code == "unauthenticated":
                log.warning("分享失败: 需要登录")
                return {"success": False, "message": "需要登录才能分享"}
            log.warning("分享失败: %s", msg)
            return {"success": False, "message": msg or "分享失败"}
        except Exception as e:
            log.error("分享漫画异常: %s", e)
            return {"success": False, "message": str(e)}

    def get_task_list(self, shared_today: bool = False) -> Optional[Dict]:
        try:
            if not self.sessdata:
                return None
            url = "https://manga.bilibili.com/twirp/user.v1.Season/GetSeasonInfo"
            resp = self.session.post(url, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                today_tasks = data.get("today_tasks", [])
                if isinstance(today_tasks, list) and today_tasks:
                    tasks = []
                    for task in today_tasks:
                        tasks.append({
                            "name": task.get("title", ""),
                            "desc": "",
                            "point": task.get("amount", 0),
                            "status": task.get("status", 0),
                            "type": task.get("type", 0),
                            "sub_id": task.get("sub_id", 0),
                            "duration": task.get("duration", 0),
                            "progress": task.get("progress", 0),
                        })
                    season_title = data.get("season_title", "")
                    season_id = data.get("season_id", "")
                    remain_amount = data.get("remain_amount", 0)
                    log.info("获取任务列表(赛季): %s, %d个任务, 积分%d", season_title, len(tasks), remain_amount)
                    return {
                        "tasks": tasks,
                        "season_title": season_title,
                        "season_id": season_id,
                        "remain_amount": remain_amount,
                    }
            checkin_status = self.get_checkin_status()
            tasks = []
            streak = 0
            if checkin_status:
                streak = checkin_status.get("streak", 0)
                points = checkin_status.get("points", [10, 20, 20, 10, 10, 10, 30])
                today_point = points[streak] if streak < len(points) else points[-1] if points else 10
                tasks.append({
                    "name": "每日签到",
                    "desc": "每日签到获取积分",
                    "point": today_point,
                    "status": 2 if checkin_status.get("today_checked") else 0,
                    "type": 100,
                    "sub_id": 0,
                    "duration": 0,
                    "progress": 0,
                })
            tasks.append({
                "name": "分享漫画",
                "desc": "每日分享漫画获取积分",
                "point": 5,
                "status": 2 if shared_today else 0,
                "type": 101,
                "sub_id": 0,
                "duration": 0,
                "progress": 0,
            })
            log.info("获取任务列表(基础): %d个任务", len(tasks))
            return {
                "tasks": tasks,
                "season_title": "",
                "season_id": "",
                "remain_amount": 0,
            }
        except Exception as e:
            log.error("获取任务列表异常: %s", e)
            return None

    def do_task(self, task_type: int, season_id: str = "") -> Optional[Dict]:
        try:
            if not self.sessdata:
                return {"success": False, "message": "未登录"}
            url = "https://manga.bilibili.com/twirp/user.v1.Season/TakeSeasonGifts"
            params = {}
            if season_id:
                params["season_id"] = season_id
            params = self._sign(params)
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            resp = self.session.post(url, data=json.dumps(params), headers=headers, timeout=15)
            result = resp.json()
            if result.get("code") == 0:
                log.info("领取赛季奖励成功")
                return {"success": True, "message": "领取成功"}
            msg = result.get("msg", "领取失败")
            if "未完成" in msg or "已领取" in msg:
                log.info("任务奖励: %s", msg)
                return {"success": False, "message": msg}
            return {"success": False, "message": msg}
        except Exception as e:
            log.error("执行任务异常: %s", e)
            return {"success": False, "message": str(e)}

    def get_user_favorites(self, page_num: int = 1, page_size: int = 20) -> Optional[Dict]:
        try:
            if not self.sessdata:
                return None
            url = "https://manga.bilibili.com/twirp/comic.v1.Favorite/ListFavorite"
            params = {"page_num": page_num, "page_size": page_size, "wait_status": 0, "sort": 0}
            params = self._sign(params)
            resp = self.session.post(url, data=params)
            result = resp.json()
            if result.get("code") == 0:
                favorites = []
                for fav in result.get("data", {}).get("list", []):
                    comic = fav.get("comic", {})
                    favorites.append({
                        "id": comic.get("id"), "title": comic.get("title", ""),
                        "cover": comic.get("vertical_cover", ""),
                        "author_name": comic.get("author_name", []),
                        "styles": comic.get("styles", []),
                        "is_finish": comic.get("is_finish", False),
                        "total": comic.get("total", 0),
                    })
                return {"favorites": favorites, "total": result.get("data", {}).get("pageInfo", {}).get("totalNum", 0)}
            return None
        except Exception as e:
            log.error("获取收藏列表异常: %s", e)
            return None

    def add_favorite(self, comic_id: int) -> bool:
        try:
            if not self.sessdata:
                return False
            url = "https://manga.bilibili.com/twirp/comic.v1.Favorite/AddFavorite"
            resp = self.session.post(url, json={"comic_id": comic_id})
            result = resp.json()
            ok = result.get("code") == 0
            if ok:
                log.info("添加收藏成功: comic_id=%d", comic_id)
            return ok
        except Exception as e:
            log.error("添加收藏异常: %s", e)
            return False
