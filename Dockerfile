# syntax=docker/dockerfile:1.4
FROM python:3.12-slim-bullseye

# Setup virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev libjpeg-dev libcairo2 gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /code

# Copy requirements & install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY ./src /code

# Copy entrypoint script
COPY ./boot/docker-run.sh /opt/run.sh
RUN chmod +x /opt/run.sh

# Expose port (optional, Compose does ports anyway)
EXPOSE 8000

# Default run
CMD ["/opt/run.sh"]
