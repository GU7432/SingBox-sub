# SingBox-sub

A small Flask app that serves sing-box JSON configs from `data/configs/` through
token-protected subscription URLs.

It also includes a password-protected web GUI at `/admin` for:

- uploading `.json` config files
- creating a blank `.json` config file
- editing config JSON in the browser
- creating named users with random tokens
- generating subscription URLs

## Project Structure

- `main.py` - app entry point
- `singbox_sub/app.py` - Flask app factory and blueprint registration
- `singbox_sub/admin.py` - admin GUI routes
- `singbox_sub/subscription.py` - `/sub` and `/healthz` routes
- `singbox_sub/storage.py` - token/config file loading, saving, and validation
- `singbox_sub/auth.py` - admin auth, client IP, and token helpers
- `singbox_sub/templates/admin.html` - admin page markup
- `singbox_sub/static/admin.css` - admin page styling
- `data/tokens.yaml` - users, tokens, and config bindings
- `data/configs/` - sing-box JSON config files
- `Dockerfile` - image build
- `docker-compose.yml` - compose deployment example

## Admin GUI

Set `ADMIN_PASSWORD` before opening `/admin`.

The admin username is always:

```text
admin
```

Example local run:

```powershell
$env:ADMIN_PASSWORD = "your-strong-password"
uv run python main.py
```

On bash-like shells:

```bash
ADMIN_PASSWORD=your-strong-password uv run python main.py
```

Then open:

```text
http://localhost:8000/admin
```

If `ADMIN_PASSWORD` is not set, `/admin` returns a setup error and does not show
the GUI.

## Subscription URL

Each user in `data/tokens.yaml` maps a username and token to a JSON config:

```yaml
users:
  gfw:
    token: "jfisobndca"
    config: "123.json"

ip_whitelist: []
min_pull_interval: 5
```

The subscription URL format is:

```text
http://localhost:8000/sub?u=gfw&t=jfisobndca
```

## Docker

Build and run locally:

```bash
docker build -t singbox-sub .
docker run --rm -p 8000:8000 -e ADMIN_PASSWORD=your-strong-password -v ./data:/app/data singbox-sub
```

## Docker Compose
Set `ADMIN_PASSWORD` in `docker-compose.yml` or through your deployment
environment before opening `/admin`.

## Notes

- Config filenames must end with `.json`.
- Uploaded and edited configs are validated as JSON before saving.
- The GUI saves JSON with indentation.
- Generated tokens are URL-safe random strings.
