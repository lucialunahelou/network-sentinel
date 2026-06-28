# Use lightweight Python 3.12 Linux base
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS-level networking diagnostics (ping, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies directly (lightweight enough to skip requirements.txt)
RUN pip install --no-cache-dir flask speedtest-cli

# Copy application source code
COPY . .

# Ensure data directory exists for SQLite
RUN mkdir -p /app/data

# Expose Flask web port
EXPOSE 5000

# Launch the master controller
CMD ["python", "app.py"]