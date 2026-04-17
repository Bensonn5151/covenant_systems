# Covenant Systems — FastAPI Backend
# Deployed on Render (free tier)
#
# Build: docker build -t covenant-api .
# Run:   docker run -p 8000:8000 covenant-api

FROM python:3.10-slim

WORKDIR /app

# System deps for PDF processing + FAISS
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Python deps — install first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ api/
COPY ingestion/ ingestion/
COPY search/ search/
COPY storage/ storage/
COPY configs/ configs/
COPY data/ data/
COPY gold_builder.py .
COPY batch_ingest.py .

# Render sets PORT env var (usually 10000)
EXPOSE 10000

# Use shell form so $PORT is expanded at runtime
CMD ["sh", "-c", "uvicorn api.fastapi.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
