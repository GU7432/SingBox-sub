FROM python:3.11-slim

# 建置時安裝系統相依套件（如需）
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製相依並安裝（利用快取）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . /app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
