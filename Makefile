# Makefile for Tipitaka ETL + Weaviate project
# Usage:
#   make up        -> start weaviate + dependencies
#   make down      -> stop containers
#   make build     -> rebuild ETL image
#   make load      -> run ETL pipeline (schema + ingestion)
#   make logs      -> follow weaviate logs

# Start services in background
up:
	docker compose up -d weaviate

# Stop services
down:
	docker compose down

# Build/rebuild ETL container
build:
	docker compose build etl

# Run ETL pipeline (one command for teammate)
load:
	docker compose run --rm etl python etl/load_weaviate.py

# Follow logs (e.g., to debug weaviate)
logs:
	docker compose logs -f weaviate
