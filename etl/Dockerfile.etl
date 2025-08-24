# Step 1: Choose a lightweight Python base
FROM python:3.11-slim

# Step 2: Set working directory inside the container
WORKDIR /app

# Step 3: Install system dependencies (optional, for psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Copy requirements first (better layer caching)
COPY etl/requirements.txt /app/requirements.txt

# Step 5: Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy your code (scripts will be mounted by docker-compose too)
COPY etl/ /app/etl
COPY data/ /app/data
COPY .env /app/.env

# Step 7: Default command (can be overridden in docker-compose) //Default entrypoint for ETL
CMD ["python", "etl/load_weaviate.py"]

