#!/usr/bin/env bash
set -euo pipefail


if [ ! -f .env ]; then
echo ".env not found; copying from .env.example"
cp .env.example .env
fi


echo "Building ETL image..."
docker compose build etl


echo "Starting core services (Postgres, t2v, Weaviate)..."
docker compose up -d postgres t2v weaviate


# Wait for Weaviate health
printf "Waiting for Weaviate to be ready"
for i in {1..60}; do
if curl -sf "http://localhost:8080/v1/.well-known/ready" >/dev/null; then
echo "\nWeaviate is ready."
break
fi
printf "."; sleep 2
if [ "$i" -eq 60 ]; then echo "\nTimed out waiting for Weaviate"; exit 1; fi
done


echo "Running ETL (initial load)..."
docker compose run --rm etl


echo "Done. Try: http://localhost:8080"