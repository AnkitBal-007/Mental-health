FROM python:3.11-slim

WORKDIR /app

# Install system libraries: ffmpeg (required by OpenAI Whisper & librosa audio decoding),
# libsndfile1 (soundfile audio I/O backend), curl (healthcheck), and gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU and Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy ML pipeline source code & models
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose ML Pipeline port
EXPOSE 8001

# Run with Uvicorn (2 workers for ML inference to conserve memory footprint)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
