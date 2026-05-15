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

- `main.py` - Flask application
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
Docker deployment is intentionally left for you to configure.

## Docker Compose
Docker Compose deployment is intentionally left for you to configure.

## Notes

- Config filenames must end with `.json`.
- Uploaded and edited configs are validated as JSON before saving.
- The GUI saves JSON with indentation.
- Generated tokens are URL-safe random strings.
