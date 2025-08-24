# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps (for numpy, pandas, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ETL scripts into image
COPY etl/ /app/etl
COPY .env /app/.env

# Default entrypoint for ETL
command: ["python", "-m", "etl.pipeline"]

