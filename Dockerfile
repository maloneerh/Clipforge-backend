# Dockerfile
# Tells Railway exactly how to build and run ClipForge.
# Using Python 3.11 slim as the base — lightweight but complete.

FROM python:3.11-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (so Docker caches this layer)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Create temp directories
RUN mkdir -p temp/downloads temp/clips

# Expose port (Railway sets $PORT automatically)
EXPOSE 8000

# Start the server
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
