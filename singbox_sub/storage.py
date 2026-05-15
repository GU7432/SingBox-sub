import os
import tempfile

import ujson as json
import yaml
from werkzeug.utils import secure_filename

from .settings import CONFIG_DIR, TOKENS_PATH


def atomic_write_text(path, content):
    path = os.fspath(path)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def load_tokens():
    if not TOKENS_PATH.exists():
        return {"users": {}, "ip_whitelist": [], "min_pull_interval": 1800}

    with TOKENS_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    data.setdefault("users", {})
    data.setdefault("ip_whitelist", [])
    data.setdefault("min_pull_interval", 1800)
    return data


def save_tokens(data):
    atomic_write_text(
        TOKENS_PATH,
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
    )


def parse_json_text(raw):
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise ValueError(f"JSON 格式錯誤：{exc}") from exc


def format_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def sanitize_config_name(name):
    raw_name = (name or "").strip()
    if not raw_name:
        raise ValueError("缺少 config 檔名")
    if raw_name != os.path.basename(raw_name) or "/" in raw_name or "\\" in raw_name:
        raise ValueError("config 檔名不可包含路徑")

    safe_name = secure_filename(raw_name)
    if not safe_name or safe_name != raw_name:
        raise ValueError("config 檔名只能包含安全字元")
    if not safe_name.lower().endswith(".json"):
        raise ValueError("config 檔名必須以 .json 結尾")
    return safe_name


def config_path(name):
    safe_name = sanitize_config_name(name)
    base = CONFIG_DIR.resolve()
    path = (base / safe_name).resolve()
    if os.path.commonpath([base, path]) != os.fspath(base):
        raise ValueError("config 路徑不合法")
    return path


def list_configs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    names = []
    for path in CONFIG_DIR.iterdir():
        try:
            safe_name = sanitize_config_name(path.name)
        except ValueError:
            continue
        if safe_name == path.name and config_path(safe_name).is_file():
            names.append(path.name)
    return sorted(names)


def load_config_text(name):
    return config_path(name).read_text(encoding="utf-8")


def load_config_json(name):
    return json.loads(load_config_text(name))
