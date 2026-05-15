from flask import Blueprint, abort, redirect, render_template, request, url_for

from .auth import admin_auth_required, generate_token, username_is_valid
from .storage import (
    atomic_write_text,
    config_path,
    format_json,
    list_configs,
    load_config_text,
    load_tokens,
    parse_json_text,
    sanitize_config_name,
    save_tokens,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_redirect(message, message_type="ok", selected_config=None):
    args = {"message": message, "type": message_type}
    if selected_config:
        args["config"] = selected_config
    return redirect(url_for("admin.index", **args))


def render_admin(message=None, message_type="ok", selected_config=None, selected_json=None):
    tokens = load_tokens()
    users = tokens.get("users", {}) or {}
    configs = list_configs()
    config_users = {config: [] for config in configs}

    for username, info in users.items():
        user_config = info.get("config")
        if user_config in config_users:
            config_users[user_config].append(username)

    selected_config = selected_config or (configs[0] if configs else None)

    if selected_config and selected_json is None:
        path = config_path(selected_config)
        if path.exists():
            selected_json = load_config_text(selected_config)
        else:
            selected_config = None
            selected_json = ""

    subscription_urls = {
        username: url_for(
            "subscription.sub",
            u=username,
            t=info.get("token", ""),
            _external=True,
        )
        for username, info in users.items()
    }

    return render_template(
        "admin.html",
        configs=configs,
        config_users=config_users,
        users=users,
        subscription_urls=subscription_urls,
        selected_config=selected_config,
        selected_json=selected_json or "",
        message=message,
        message_type=message_type,
    )


@admin_bp.route("")
@admin_auth_required
def index():
    selected_config = request.args.get("config") or None
    message = request.args.get("message") or None
    message_type = request.args.get("type") or "ok"
    try:
        if selected_config:
            selected_config = sanitize_config_name(selected_config)
        return render_admin(message, message_type, selected_config)
    except ValueError as exc:
        return render_admin(str(exc), "error")


@admin_bp.route("/configs/upload", methods=["POST"])
@admin_auth_required
def upload_config():
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


@admin_bp.route("/configs/new", methods=["POST"])
@admin_auth_required
def new_config():
    try:
        name = sanitize_config_name(request.form.get("name"))
        path = config_path(name)
        if path.exists():
            raise ValueError("config 檔案已存在")
        atomic_write_text(path, "{}\n")
    except ValueError as exc:
        return admin_redirect(str(exc), "error")

    return admin_redirect(f"已建立空白 config：{name}", selected_config=name)


@admin_bp.route("/configs/<path:name>")
@admin_auth_required
def load_config(name):
    try:
        name = sanitize_config_name(name)
        if not config_path(name).exists():
            abort(404)
    except ValueError:
        abort(404)
    return redirect(url_for("admin.index", config=name))


@admin_bp.route("/configs/<path:name>/delete", methods=["POST"])
@admin_auth_required
def delete_config(name):
    try:
        name = sanitize_config_name(name)
        path = config_path(name)
        if not path.exists():
            return admin_redirect("找不到指定 config。", "error")

        users = load_tokens().get("users", {}) or {}
        used_by = [
            username
            for username, info in users.items()
            if info.get("config") == name
        ]
        if used_by:
            names = ", ".join(sorted(used_by))
            return admin_redirect(f"無法刪除，這個 config 正在被使用者使用：{names}", "error", name)

        path.unlink()
    except ValueError as exc:
        return admin_redirect(str(exc), "error")

    return admin_redirect(f"已刪除 config：{name}")


@admin_bp.route("/configs/<path:name>", methods=["POST"])
@admin_auth_required
def save_config(name):
    raw = request.form.get("json_text", "")
    try:
        name = sanitize_config_name(name)
        parsed = parse_json_text(raw)
        atomic_write_text(config_path(name), format_json(parsed) + "\n")
    except ValueError as exc:
        return render_admin(str(exc), "error", selected_config=name, selected_json=raw), 400

    return admin_redirect(f"已儲存 config：{name}", selected_config=name)


@admin_bp.route("/users", methods=["POST"])
@admin_auth_required
def users():
    username = (request.form.get("username") or "").strip()
    selected_config = request.form.get("config") or ""
    token = (request.form.get("token") or "").strip()
    should_generate = request.form.get("generate_token") == "1"

    try:
        selected_config = sanitize_config_name(selected_config)
        if not config_path(selected_config).exists():
            raise ValueError("指定的 config 不存在")
        if not username_is_valid(username):
            raise ValueError("使用者名稱只能包含英數字、底線、連字號與句點，長度最多 64")
        if should_generate or not token:
            token = generate_token()

        tokens = load_tokens()
        tokens.setdefault("users", {})
        tokens["users"][username] = {"token": token, "config": selected_config}
        save_tokens(tokens)
    except ValueError as exc:
        return admin_redirect(str(exc), "error", selected_config=selected_config)

    return admin_redirect(f"已儲存使用者：{username}", selected_config=selected_config)


@admin_bp.route("/users/<name>/delete", methods=["POST"])
@admin_auth_required
def delete_user(name):
    tokens = load_tokens()
    users = tokens.setdefault("users", {})
    if name in users:
        users.pop(name)
        save_tokens(tokens)
        return admin_redirect(f"已刪除使用者：{name}")
    return admin_redirect("找不到指定使用者。", "error")
