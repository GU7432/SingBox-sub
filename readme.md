# SingBox-sub

簡單的 Flask 應用，用來根據 `data/tokens.yaml` 與 `data/configs/` 回傳對應的設定 JSON。此專案已提供 Dockerfile 與 `docker-compose.yml`，可以快速建置與在容器中執行。

## 目錄結構（重點）
- `app.py` - Flask 應用入口
- `requirements.txt` - Python 相依
- `data/` - 放 tokens.yaml 與 configs
- `Dockerfile` - 建置映像檔用
- `docker-compose.yml` - 方便開發/啟動

---

## 先決條件
- 已安裝 Docker（或 Podman）
- 若使用 `docker compose`，請安裝 Docker Compose v2（或 `docker-compose`）

## 本地用 Docker 建置與執行

1. 在專案根目錄執行建置：

```bash
docker build -t singboxsub:1.0 .
```

2. 背景（detached）執行容器：

```bash
docker run -d --name singboxsub -p 8000:8000 -v "$(pwd)/data:/app/data:ro" singboxsub:1.0
```

說明：
- `-d`：背景執行
- `--name singboxsub`：容器名稱，方便管理
- `-v "$(pwd)/data:/app/data:ro"`：把本機的 `data` 掛載到容器（唯讀）。若容器需寫入請移除 `:ro`。

停止/查看日誌/移除容器：

```bash
docker logs -f singboxsub
docker stop singboxsub
docker rm singboxsub
```

---

## 使用 docker-compose（推薦開發）

專案內已提供 `docker-compose.yml`，直接使用：

```bash
# 若使用 Docker Compose v2
docker compose up -d --build
# 或舊版 docker-compose
docker-compose up -d --build
```

關閉並移除服務：

```bash
docker compose down
```

---

## Smoke test（健康檢查）

1. 檢查服務是否存活：

```bash
curl http://127.0.0.1:8000/healthz
# 預期回傳: ok
```

2. 測試主 API（需根據 `data/tokens.yaml` 裡的 user/token 填入）：

```bash
curl 'http://127.0.0.1:8000/sub?u=<user>&t=<token>'
```


