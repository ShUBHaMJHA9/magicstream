FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Install FFmpeg, librsvg for vector SVG rendering, and system fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    librsvg2-bin \
    fonts-dejavu-core \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt pyproject.toml setup.py /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and assets
COPY . /app/
RUN pip install --no-cache-dir .

# Expose Web Dashboard & REST API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default execution entrypoint: runs magicstream
CMD ["magicstream"]
