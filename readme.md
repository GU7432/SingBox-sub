# SingBox-sub

簡單的 Flask 應用，用來根據 `data/tokens.yaml` 與 `data/configs/` 回傳對應的設定 JSON。

目前可直接使用已編譯完成的映像：`guaaaan244/singboxsub:v1.0`，不需要自行建置。

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

## 直接使用預編譯映像執行

1. 拉取映像：

```bash
docker pull guaaaan244/singboxsub:v1.0
```

2. 背景（detached）執行容器：

```bash
docker run -d --name singboxsub -p 8000:8000 -v "$(pwd)/data:/app/data:ro" guaaaan244/singboxsub:v1.0
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

## 使用 docker-compose（選用）

若要用 compose 啟動，請先把 `docker-compose.yml` 內的：

```yaml
build: .
```

改成：

```yaml
image: guaaaan244/singboxsub:v1.0
```

然後執行：

```bash
# 若使用 Docker Compose v2
docker compose up -d
# 或舊版 docker-compose
docker-compose up -d
```

關閉並移除服務：

```bash
docker compose down
```



