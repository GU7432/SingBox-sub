import hashlib
import time

from flask import Blueprint, Response, abort, request
import ujson as json

from .auth import client_ip
from .storage import config_path, load_config_json, load_config_text, load_tokens

subscription_bp = Blueprint("subscription", __name__)

# Simple in-memory pull throttle.
_last_pull = {}


@subscription_bp.route("/sub")
def sub():
    cfg = load_tokens()
    users = cfg.get("users", {})
    ip_allow = cfg.get("ip_whitelist", []) or []
    min_gap = int(cfg.get("min_pull_interval", 1800))

    username = request.args.get("u", "").strip()
    token = request.args.get("t", "").strip()
    ip = client_ip()

    if ip_allow and ip not in ip_allow:
        abort(403)
    if username not in users or users[username]["token"] != token:
        abort(403)

    now = int(time.time())
    last = _last_pull.get(username, 0)
    if now - last < min_gap:
        return Response("Too frequent", status=429)
    _last_pull[username] = now

    config_name = users[username].get("config")
    try:
        path = config_path(config_name)
    except ValueError:
        abort(404)
    if not path.exists():
        abort(404)

    raw = load_config_text(config_name)
    config_data = load_config_json(config_name)
    version_hash = hashlib.sha256(
        json.dumps(config_data, sort_keys=True).encode()
    ).hexdigest()[:16]

    if request.headers.get("If-None-Match") == version_hash:
        return Response(status=304)

    response = Response(raw, mimetype="application/json")
    response.headers["ETag"] = version_hash
    response.headers["Cache-Control"] = "no-store"
    return response


@subscription_bp.route("/healthz")
def healthz():
    return "ok"
