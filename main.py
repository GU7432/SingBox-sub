from functools import wraps
import hashlib
import os
import secrets
import tempfile
import time

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template_string,
    request,
    url_for,
)
import yaml
import ujson as json
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

BASE_DIR = os.path.dirname(__file__)
TOKENS_PATH = os.path.join(BASE_DIR, "data", "tokens.yaml")
CONFIG_DIR = os.path.join(BASE_DIR, "data", "configs")

# Simple in-memory pull throttle.
_last_pull = {}


ADMIN_TEMPLATE = """
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SingBox-sub Admin</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, "Microsoft JhengHei", "Noto Sans TC", sans-serif;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #65717e;
      --line: #d9e0e8;
      --primary: #1769aa;
      --danger: #b3261e;
      --ok: #0f7b3f;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--text); }
    header {
      padding: 22px clamp(16px, 4vw, 40px);
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 { margin: 0 0 6px; font-size: 24px; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 420px) minmax(0, 1fr);
      gap: 18px;
      padding: 18px clamp(16px, 4vw, 40px) 36px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .stack { display: grid; gap: 18px; }
    .message {
      margin: 18px clamp(16px, 4vw, 40px) 0;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--primary);
      border-radius: 6px;
      background: var(--panel);
    }
    .message.error { border-left-color: var(--danger); }
    label { display: block; margin: 10px 0 6px; color: var(--muted); font-size: 13px; }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      background: #fff;
      color: var(--text);
    }
    textarea {
      min-height: 520px;
      resize: vertical;
      font-family: Consolas, "Courier New", monospace;
      font-size: 14px;
      line-height: 1.45;
    }
    button, .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 36px;
      border: 1px solid var(--primary);
      border-radius: 6px;
      padding: 8px 12px;
      background: var(--primary);
      color: #fff;
      font: inherit;
      text-decoration: none;
      cursor: pointer;
    }
    button.secondary, .button.secondary {
      background: #fff;
      color: var(--primary);
    }
    button.danger {
      border-color: var(--danger);
      background: var(--danger);
    }
    .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .space { justify-content: space-between; }
    .list { display: grid; gap: 10px; }
    .item {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfd;
    }
    .item strong { display: block; margin-bottom: 4px; }
    .small { color: var(--muted); font-size: 13px; word-break: break-all; }
    code {
      display: block;
      margin-top: 8px;
      padding: 8px;
      border-radius: 6px;
      background: #eef3f8;
      color: #1b3347;
      word-break: break-all;
    }
    form.inline { display: inline; }
    .editor-head { margin-bottom: 10px; }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      textarea { min-height: 360px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>SingBox-sub Admin</h1>
    <p>管理 configs、使用者 token，並產生訂閱網址。</p>
  </header>

  {% if message %}
    <div class="message {{ 'error' if message_type == 'error' else '' }}">{{ message }}</div>
  {% endif %}

  <main>
    <div class="stack">
      <section>
        <h2>建立或更新使用者</h2>
        <form method="post" action="{{ url_for('admin_users') }}">
          <label for="username">使用者名稱</label>
          <input id="username" name="username" required pattern="[A-Za-z0-9_.-]{1,64}" placeholder="gfw">

          <label for="config">Config</label>
          <select id="config" name="config" required>
            {% for config in configs %}
              <option value="{{ config }}">{{ config }}</option>
            {% endfor %}
          </select>

          <label for="token">Token</label>
          <input id="token" name="token" placeholder="留空會自動產生">
          <label class="row">
            <input type="checkbox" name="generate_token" value="1" checked style="width:auto">
            自動產生隨機 token
          </label>

          <div class="row" style="margin-top: 12px;">
            <button type="submit">儲存使用者</button>
          </div>
        </form>
      </section>

      <section>
        <h2>上傳 Config</h2>
        <form method="post" action="{{ url_for('admin_upload_config') }}" enctype="multipart/form-data">
          <label for="file">JSON 檔案</label>
          <input id="file" type="file" name="file" accept=".json,application/json" required>
          <div class="row" style="margin-top: 12px;">
            <button type="submit">上傳</button>
          </div>
        </form>
      </section>

      <section>
        <h2>新增空白 Config</h2>
        <form method="post" action="{{ url_for('admin_new_config') }}">
          <label for="new_config_name">檔名</label>
          <input id="new_config_name" name="name" required placeholder="new-config.json">
          <div class="row" style="margin-top: 12px;">
            <button type="submit">建立空白檔案</button>
          </div>
        </form>
      </section>

      <section>
        <h2>使用者與網址</h2>
        <div class="list">
          {% for username, info in users.items() %}
            <div class="item">
              <div class="row space">
                <strong>{{ username }}</strong>
                <form class="inline" method="post" action="{{ url_for('admin_delete_user', name=username) }}">
                  <button class="danger" type="submit">刪除</button>
                </form>
              </div>
              <div class="small">Config: {{ info.config }}</div>
              <div class="small">Token: {{ info.token }}</div>
              <code>{{ subscription_urls[username] }}</code>
            </div>
          {% else %}
            <p>尚未建立使用者。</p>
          {% endfor %}
        </div>
      </section>
    </div>

    <section>
      <div class="editor-head row space">
        <h2>Config 編輯器</h2>
        <form method="get" action="{{ url_for('admin_index') }}" class="row">
          <select name="config">
            {% for config in configs %}
              <option value="{{ config }}" {% if config == selected_config %}selected{% endif %}>{{ config }}</option>
            {% endfor %}
          </select>
          <button class="secondary" type="submit">載入</button>
        </form>
      </div>

      {% if selected_config %}
        <form method="post" action="{{ url_for('admin_save_config', name=selected_config) }}">
          <label for="json_text">正在編輯：{{ selected_config }}</label>
          <textarea id="json_text" name="json_text" spellcheck="false">{{ selected_json }}</textarea>
          <div class="row" style="margin-top: 12px;">
            <button type="submit">驗證並儲存</button>
            <a class="button secondary" href="{{ url_for('admin_load_config', name=selected_config) }}">重新載入</a>
          </div>
        </form>
      {% else %}
        <p>先上傳一個 `.json` config，或從左側選擇現有檔案。</p>
      {% endif %}
    </section>
  </main>
</body>
</html>
"""


def load_tokens():
    if not os.path.exists(TOKENS_PATH):
        return {"users": {}, "ip_whitelist": [], "min_pull_interval": 1800}
    with open(TOKENS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("users", {})
    data.setdefault("ip_whitelist", [])
    data.setdefault("min_pull_interval", 1800)
    return data


def atomic_write_text(path, content):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def save_tokens(data):
    atomic_write_text(
        TOKENS_PATH,
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
    )


def parse_json_text(raw):
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise ValueError(f"JSON 格式錯誤：{exc}") from exc
    return parsed


def format_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def list_configs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    names = []
    for name in os.listdir(CONFIG_DIR):
        try:
            safe_name = sanitize_config_name(name)
        except ValueError:
            continue
        if safe_name == name and os.path.isfile(config_path(safe_name)):
            names.append(name)
    return sorted(names)


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
    base = os.path.abspath(CONFIG_DIR)
    path = os.path.abspath(os.path.join(base, safe_name))
    if os.path.commonpath([base, path]) != base:
        raise ValueError("config 路徑不合法")
    return path


def generate_token():
    return secrets.token_urlsafe(64)


def admin_password():
    return os.environ.get("ADMIN_PASSWORD", "")


def admin_auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        password = admin_password()
        if not password:
            return Response(
                "ADMIN_PASSWORD is not set. Set it before using /admin.",
                status=503,
                mimetype="text/plain",
            )

        auth = request.authorization
        if not auth or auth.username != "admin" or not secrets.compare_digest(auth.password, password):
            return Response(
                "Authentication required",
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="SingBox-sub Admin"'},
                mimetype="text/plain",
            )
        return view(*args, **kwargs)

    return wrapped


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def username_is_valid(username):
    return bool(username) and len(username) <= 64 and all(
        ch.isalnum() or ch in "_.-" for ch in username
    )


def admin_redirect(message, message_type="ok", selected_config=None):
    args = {"message": message, "type": message_type}
    if selected_config:
        args["config"] = selected_config
    return redirect(url_for("admin_index", **args))


def render_admin(message=None, message_type="ok", selected_config=None, selected_json=None):
    tokens = load_tokens()
    users = tokens.get("users", {}) or {}
    configs = list_configs()
    selected_config = selected_config or (configs[0] if configs else None)

    if selected_config and selected_json is None:
        path = config_path(selected_config)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                selected_json = f.read()
        else:
            selected_config = None
            selected_json = ""

    subscription_urls = {
        username: url_for(
            "sub",
            u=username,
            t=info.get("token", ""),
            _external=True,
        )
        for username, info in users.items()
    }

    return render_template_string(
        ADMIN_TEMPLATE,
        configs=configs,
        users=users,
        subscription_urls=subscription_urls,
        selected_config=selected_config,
        selected_json=selected_json or "",
        message=message,
        message_type=message_type,
    )


@app.route("/admin")
@admin_auth_required
def admin_index():
    selected_config = request.args.get("config") or None
    message = request.args.get("message") or None
    message_type = request.args.get("type") or "ok"
    try:
        if selected_config:
            selected_config = sanitize_config_name(selected_config)
        return render_admin(message, message_type, selected_config)
    except ValueError as exc:
        return render_admin(str(exc), "error")


@app.route("/admin/configs/upload", methods=["POST"])
@admin_auth_required
def admin_upload_config():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return admin_redirect("請選擇要上傳的 JSON 檔案。", "error")

    try:
        name = sanitize_config_name(uploaded.filename)
        raw = uploaded.read().decode("utf-8")
        parsed = parse_json_text(raw)
        atomic_write_text(config_path(name), format_json(parsed) + "\n")
    except (UnicodeDecodeError, ValueError) as exc:
        return admin_redirect(str(exc), "error")

    return admin_redirect(f"已上傳 config：{name}", selected_config=name)


@app.route("/admin/configs/new", methods=["POST"])
@admin_auth_required
def admin_new_config():
    try:
        name = sanitize_config_name(request.form.get("name"))
        path = config_path(name)
        if os.path.exists(path):
            raise ValueError("config 檔案已存在")
        atomic_write_text(path, "{}\n")
    except ValueError as exc:
        return admin_redirect(str(exc), "error")

    return admin_redirect(f"已建立空白 config：{name}", selected_config=name)


@app.route("/admin/configs/<path:name>")
@admin_auth_required
def admin_load_config(name):
    try:
        name = sanitize_config_name(name)
        if not os.path.exists(config_path(name)):
            abort(404)
    except ValueError:
        abort(404)
    return redirect(url_for("admin_index", config=name))


@app.route("/admin/configs/<path:name>", methods=["POST"])
@admin_auth_required
def admin_save_config(name):
    raw = request.form.get("json_text", "")
    try:
        name = sanitize_config_name(name)
        parsed = parse_json_text(raw)
        pretty = format_json(parsed) + "\n"
        atomic_write_text(config_path(name), pretty)
    except ValueError as exc:
        return render_admin(str(exc), "error", selected_config=name, selected_json=raw), 400

    return admin_redirect(f"已儲存 config：{name}", selected_config=name)


@app.route("/admin/users", methods=["POST"])
@admin_auth_required
def admin_users():
    username = (request.form.get("username") or "").strip()
    selected_config = request.form.get("config") or ""
    token = (request.form.get("token") or "").strip()
    generate = request.form.get("generate_token") == "1"

    try:
        selected_config = sanitize_config_name(selected_config)
        if not os.path.exists(config_path(selected_config)):
            raise ValueError("指定的 config 不存在")
        if not username_is_valid(username):
            raise ValueError("使用者名稱只能包含英數字、底線、連字號與點，長度最多 64")
        if generate or not token:
            token = generate_token()
        tokens = load_tokens()
        tokens.setdefault("users", {})
        tokens["users"][username] = {"token": token, "config": selected_config}
        save_tokens(tokens)
    except ValueError as exc:
        return admin_redirect(str(exc), "error", selected_config=selected_config)

    return admin_redirect(f"已儲存使用者：{username}", selected_config=selected_config)


@app.route("/admin/users/<name>/delete", methods=["POST"])
@admin_auth_required
def admin_delete_user(name):
    tokens = load_tokens()
    users = tokens.setdefault("users", {})
    if name in users:
        users.pop(name)
        save_tokens(tokens)
        return admin_redirect(f"已刪除使用者：{name}")
    return admin_redirect("找不到指定使用者。", "error")


@app.route("/sub")
def sub():
    cfg = load_tokens()
    users = cfg.get("users", {})
    ip_allow = cfg.get("ip_whitelist", []) or []
    min_gap = int(cfg.get("min_pull_interval", 1800))

    u = request.args.get("u", "").strip()
    t = request.args.get("t", "").strip()
    ip = client_ip()

    # Verify IP allowlist.
    if ip_allow and ip not in ip_allow:
        abort(403)

    # Verify user token.
    if u not in users or users[u]["token"] != t:
        abort(403)

    # Throttle pulls.
    now = int(time.time())
    last = _last_pull.get(u, 0)
    if now - last < min_gap:
        return Response("Too frequent", status=429)
    _last_pull[u] = now

    user_conf = users[u].get("config")
    try:
        conf_path = config_path(user_conf)
    except ValueError:
        abort(404)
    if not os.path.exists(conf_path):
        abort(404)

    with open(conf_path, "r", encoding="utf-8") as f:
        raw = f.read()
    config_data = json.loads(raw)

    version_hash = hashlib.sha256(
        json.dumps(config_data, sort_keys=True).encode()
    ).hexdigest()[:16]

    if request.headers.get("If-None-Match") == version_hash:
        return Response(status=304)

    resp = Response(raw, mimetype="application/json")
    resp.headers["ETag"] = version_hash
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
