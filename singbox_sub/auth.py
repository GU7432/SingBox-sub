from functools import wraps
import os
import secrets

from flask import Response, request


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
        provided_password = auth.password if auth and auth.password is not None else ""
        password_matches = secrets.compare_digest(provided_password, password)
        if not auth or auth.username != "admin" or not password_matches:
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


def generate_token():
    return secrets.token_urlsafe(64)


def username_is_valid(username):
    return bool(username) and len(username) <= 64 and all(
        ch.isalnum() or ch in "_.-" for ch in username
    )
