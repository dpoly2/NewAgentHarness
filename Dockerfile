# ArchonHub Hub Server
# =====================
# Runs the FastAPI hub server on port 8765.
# All data is persisted via a volume mount at /app/memory and /app/data.

FROM python:3.13-slim

WORKDIR /app

# System deps for PyMuPDF, Pillow, chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps first (layer cache)
COPY .agents/agentharness/app/v3/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY .agents/agentharness/app/v3/ ./

# Create data directories
RUN mkdir -p /app/memory /app/data/logs /app/data/backup

# Expose hub server port
EXPOSE 8765

# Environment defaults (override via docker-compose or -e flags)
ENV HUB_PORT=8765 \
    HUB_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1

CMD ["python", "hub_server.py"]
