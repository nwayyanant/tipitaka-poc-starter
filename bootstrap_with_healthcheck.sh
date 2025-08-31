#!/usr/bin/env bash
set -e

# -----------------------------
# CONFIGURATION
# -----------------------------
EMBEDDING_SCALE=${EMBEDDING_SCALE:-2}        # number of embedding service replicas
WEAVIATE_PORT=${WEAVIATE_PORT:-8080}        # Weaviate HTTP port
WEAVIATE_GRPC_PORT=${WEAVIATE_GRPC_PORT:-50051}

echo "🚀 Step 1: Build Docker images..."
docker compose build

# -----------------------------
# Start Weaviate
# -----------------------------
echo "🟢 Step 2: Start Weaviate..."
docker compose up -d weaviate

# Wait for Weaviate to become ready
echo "⏳ Waiting for Weaviate to be ready..."
until curl -s http://localhost:${WEAVIATE_PORT}/v1/.well-known/ready > /dev/null; do
    echo "Waiting for Weaviate..."
    sleep 3
done
echo "✅ Weaviate is ready."

# -----------------------------
# Start embedding service
# -----------------------------
echo "🟢 Step 3: Start embedding service with ${EMBEDDING_SCALE} replicas..."
docker compose up -d --scale embedding=${EMBEDDING_SCALE}

# Wait for all embedding replicas to respond to /health
echo "⏳ Waiting for embedding service replicas..."
for i in $(seq 1 ${EMBEDDING_SCALE}); do
    REPLICA="embedding_${i}"
    echo "Checking replica $i ($REPLICA)..."
    RETRY=0
    until curl -s http://localhost:8000/health > /dev/null; do
        RETRY=$((RETRY+1))
        if [ $RETRY -gt 20 ]; then
            echo "❌ Replica $i not responding after 20 retries. Exiting."
            exit 1
        fi
        sleep 3
    done
    echo "✅ Replica $i is ready."
done

# -----------------------------
# Optional: initialize Weaviate schema
# -----------------------------
SCHEMA_SCRIPT="./weaviate-setup/create_schema.py"
if [ -f "$SCHEMA_SCRIPT" ]; then
    echo "📦 Step 4: Initialize Weaviate schema..."
    docker compose run --rm \
      -e WEAVIATE_URL=http://weaviate:8080 \
      python:3.10-slim bash -c "pip install --no-cache-dir weaviate-client && python /workdir/weaviate-setup/create_schema.py"
else
    echo "Skipping schema initialization (no create_schema.py found)."
fi

# -----------------------------
# Run example search CLI
# -----------------------------
echo "🔎 Step 5: Run a sample search query..."
docker compose run --rm search \
    --collection Window \
    --mode hybrid \
    --query "mettā and compassion" \
    --k 5 \
    --alpha 0.5

echo "✅ Bootstrap complete!"
