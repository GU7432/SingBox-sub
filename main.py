from flask import Flask, request, Response, abort
import yaml, ujson as json, time, os, hashlib

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
TOKENS_PATH = os.path.join(BASE_DIR, "data", "tokens.yaml")
CONFIG_DIR = os.path.join(BASE_DIR, "data", "configs")

# 簡易緩存拉取時間（避免濫刷）
_last_pull = {}

def load_tokens():
    with open(TOKENS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())

def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

@app.route("/sub")
def sub():
    cfg = load_tokens()
    users = cfg.get("users", {})
    ip_allow = cfg.get("ip_whitelist", []) or []
    min_gap = int(cfg.get("min_pull_interval", 1800))

    u = request.args.get("u", "").strip()
    t = request.args.get("t", "").strip()
    ip = client_ip()

    # 驗證 IP
    if ip_allow and ip not in ip_allow:
        abort(403)

    # 驗證使用者/Token
    if u not in users or users[u]["token"] != t:
        abort(403)

    # 驗證拉取間隔
    now = int(time.time())
    last = _last_pull.get(u, 0)
    if now - last < min_gap:
        return Response("Too frequent", status=429)
    _last_pull[u] = now

    # 載入對應配置檔
    user_conf = users[u].get("config")
    conf_path = os.path.join(CONFIG_DIR, user_conf)
    if not os.path.exists(conf_path):
        abort(404)

    # 讀取原始檔案內容（不要在回傳中加入額外欄位）
    with open(conf_path, "r", encoding="utf-8") as f:
        raw = f.read()
    # 解析為資料結構以生成穩定的版本雜湊（ETag），但不改變 raw 內容
    config_data = json.loads(raw)

    # 生成版本雜湊（ETag）以支援快取
    version_hash = hashlib.sha256(json.dumps(config_data, sort_keys=True).encode()).hexdigest()[:16]

    # ETag 支援（快取）
    if request.headers.get("If-None-Match") == version_hash:
        return Response(status=304)

    # 回傳原始 JSON 檔案內容，不加入 _meta
    resp = Response(raw, mimetype="application/json")
    resp.headers["ETag"] = version_hash
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/healthz")
def healthz():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
