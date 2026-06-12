python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements and install in stages
# (splitting reduces chance of timeout)
COPY requirements.txt .

# Install heavy packages first separately
RUN pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu

# Install the rest
RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    uvicorn[standard]==0.29.0 \
    python-multipart==0.0.9 \
    yt-dlp==2024.5.27 \
    openai-whisper==20231117 \
    anthropic==0.28.0 \
    python-dotenv==1.0.1 \
    aiofiles==23.2.1 \
    httpx==0.27.0

# Copy all code
COPY . .

# Create temp directories
RUN mkdir -p temp/downloads temp/clips

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
