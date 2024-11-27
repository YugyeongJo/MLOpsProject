FROM python:3.11.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY app/dependencies.txt .
RUN pip install --no-cache-dir -r dependencies.txt

# 앱 파일 복사
COPY app/ .

# 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]