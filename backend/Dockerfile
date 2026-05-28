FROM python:3.11-slim

WORKDIR /app

# System deps for PaddleOCR + PDF processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-tam \
    tesseract-ocr-tel \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Updated to look into PyTorch's official repository for CPU builds
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]