FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY app/dependencies.txt .
RUN pip install --no-cache-dir -r dependencies.txt

COPY app/model/ /app/model/

RUN python -c "import torch; torch.hub.load('ultralytics/yolov5', 'custom', path='model/best_yolo_model_defect.pt', force_reload=True)"

COPY app/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]