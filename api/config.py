import json
import os

_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def load_config() -> dict:
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict):
    try:
        os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")


def get_login_credentials() -> dict:
    config = load_config()
    sessdata = config.get("sessdata", "")
    bili_jct = config.get("bili_jct", "")
    user_info = config.get("user_info", {})
    if sessdata:
        return {
            "sessdata": sessdata,
            "bili_jct": bili_jct,
            "user_info": user_info,
        }
    return {}


def save_login_credentials(sessdata: str, bili_jct: str = "", user_info: dict = None):
    config = load_config()
    config["sessdata"] = sessdata
    if bili_jct:
        config["bili_jct"] = bili_jct
    if user_info:
        config["user_info"] = user_info
    save_config(config)


def clear_login_credentials():
    config = load_config()
    config.pop("sessdata", None)
    config.pop("bili_jct", None)
    config.pop("user_info", None)
    save_config(config)


def save_setting(key: str, value):
    config = load_config()
    if "settings" not in config:
        config["settings"] = {}
    config["settings"][key] = value
    save_config(config)


def get_setting(key: str, default=None):
    config = load_config()
    return config.get("settings", {}).get(key, default)
