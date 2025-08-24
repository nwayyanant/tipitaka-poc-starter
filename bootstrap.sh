#!/usr/bin/env bash
# bootstrap.sh (cross-platform startup script)
# -------------
# Convenience script to set up and run the Tipitaka ETL + Weaviate pipeline. 
# Usage:
#   ./bootstrap.sh up       -> start weaviate
#   ./bootstrap.sh down     -> stop containers
#   ./bootstrap.sh build    -> rebuild ETL image
#   ./bootstrap.sh load     -> run ETL pipeline (schema + ingestion)
#   ./bootstrap.sh logs     -> follow weaviate logs

set -e  # exit immediately if a command fails

CMD=$1

case "$CMD" in
  up)
    echo "🚀 Starting Weaviate..."
    docker compose up -d weaviate
    ;;
  down)
    echo "🛑 Stopping containers..."
    docker compose down
    ;;
  build)
    echo "🔨 Building ETL container..."
    docker compose build etl
    ;;
  load)
    echo "📥 Running ETL pipeline (schema + ingestion)..."
    docker compose run --rm etl python etl/load_weaviate.py
    ;;
  logs)
    echo "📜 Following Weaviate logs..."
    docker compose logs -f weaviate
    ;;
  *)
    echo "Usage: ./bootstrap.sh {up|down|build|load|logs}"
    exit 1
    ;;
esac
