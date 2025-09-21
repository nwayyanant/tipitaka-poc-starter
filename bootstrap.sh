#!/usr/bin/env bash
# bootstrap.sh — one-click helpers for Weaviate + Embedding Service + ETL pipeline
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="dev"
if [[ "${2:-}" == "--prod" ]]; then
  MODE="prod"
  shift
fi

COMPOSE_FILES="-f docker-compose.yml"

if [[ "$MODE" == "prod" ]]; then
  COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
else
  # dev mode → include override for hot-reload
  if [[ -f docker-compose.override.yml ]]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.override.yml"
  fi
fi

# Detect docker compose v2 vs v1
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose $COMPOSE_FILES"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose $COMPOSE_FILES"
else
  echo "❌ docker compose not found" >&2
  exit 1
fi

# Default ports
WEAVIATE_HOST_PORT="${WEAVIATE_HOST_PORT:-8090}"
WEAVIATE_GRPC_HOST_PORT="${WEAVIATE_GRPC_HOST_PORT:-50051}"
EMBEDDING_HOST_PORT="${EMBEDDING_HOST_PORT:-8000}"
SEARCH_HOST_PORT="${SEARCH_HOST_PORT:-8002}"

usage() {
  cat <<EOF
Usage: ./bootstrap.sh {setup|up|build|load|logs|down|ps} [--prod]

Options:
  --prod : use docker-compose.prod.yml (preloaded models, no bind-mounts)

Commands:
  setup  : up → build → load
  up     : start Weaviate + Embedding + Search
  build  : build ETL + Embedding + Search images
  load   : run ETL pipeline
  logs   : follow logs
  down   : stop and remove containers/volumes
  ps     : show running containers

Env (optional):
  WEAVIATE_HOST_PORT       (default: 8090)
  WEAVIATE_GRPC_HOST_PORT  (default: 50051)
  EMBEDDING_HOST_PORT      (default: 8000)
  SEARCH_HOST_PORT         (default: 8002)
EOF
}

wait_for_service() {
  local name="$1"
  local url="$2"
  local max_wait="${3:-120}"
  local waited=0
  local delay=2

  echo "⏳ Waiting for $name ($url)..."

  until curl -fsSL "$url" >/dev/null 2>&1; do
    sleep "$delay"
    waited=$((waited+delay))
    if [ "$waited" -ge "$max_wait" ]; then
      echo "❌ Timeout: $name not ready after ${max_wait}s" >&2
      exit 1
    fi
    if [ "$delay" -lt 10 ]; then
      delay=$((delay*2))
    fi
  done
  echo "✅ $name ready after ${waited}s."
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP -sTCP:LISTEN -P | grep -q ":${port} "
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ano 2>/dev/null | grep -q ":${port} "
  else
    return 1
  fi
}

check_ports() {
  for p in "$WEAVIATE_HOST_PORT" "$WEAVIATE_GRPC_HOST_PORT" "$EMBEDDING_HOST_PORT"; do
    if port_in_use "$p"; then
      echo "⚠️  Port ${p} looks in use on host. If compose fails, edit docker-compose.yml to map a free port."
    fi
  done
}

# ---- commands -------------------------------------------------------------

cmd_up() {
  echo "🚀 Starting services (weaviate + embedding + search)…"
  (cd "$PROJECT_ROOT" && $COMPOSE up -d --remove-orphans weaviate embedding search)
  echo "✅ Services started."
  echo "   Weaviate REST:   http://localhost:${WEAVIATE_HOST_PORT}/v1/graphql"
  echo "   Weaviate gRPC:   localhost:${WEAVIATE_GRPC_HOST_PORT}"
  echo "   Embedding API:   http://localhost:${EMBEDDING_HOST_PORT}/embed"
  echo "   Search API:      http://localhost:${SEARCH_HOST_PORT}/search"
}

cmd_build() {
  echo "🔧 Building images (etl + embedding + search)…"
  (cd "$PROJECT_ROOT" && $COMPOSE build etl embedding search)
  echo "✅ Images built."
}

cmd_load() {
  echo "📦 Running ETL pipeline (schema + CSV + vectors + sanity)…"
  wait_for_service "Weaviate" "http://localhost:${WEAVIATE_HOST_PORT}/v1/.well-known/ready" 300
  wait_for_service "Embedding Service" "http://localhost:${EMBEDDING_HOST_PORT}/health" 600
  wait_for_service "Search Service" "http://localhost:${SEARCH_HOST_PORT}/health" 120
  (cd "$PROJECT_ROOT" && $COMPOSE run --rm etl)
  echo "✅ Data load finished."
}

cmd_logs() {
  echo "🪵 Tailing logs…"
  (cd "$PROJECT_ROOT" && $COMPOSE logs -f weaviate embedding search etl || true)
}

cmd_down() {
  echo "🧹 Stopping & removing containers (and volumes)…"
  (cd "$PROJECT_ROOT" && $COMPOSE down -v)
  echo "✅ Done."
}

cmd_ps() {
  (cd "$PROJECT_ROOT" && $COMPOSE ps)
}

cmd_setup() {
  cmd_up
  cmd_build
  cmd_load
  echo "🎉 Setup complete. Open GraphQL: http://localhost:${WEAVIATE_HOST_PORT}/v1/graphql"
}

# ---- dispatcher -----------------------------------------------------------

main() {
  local action="${1:-}"
  case "$action" in
    setup) cmd_setup ;;
    up)    cmd_up ;;
    build) cmd_build ;;
    load)  cmd_load ;;
    logs)  cmd_logs ;;
    down)  cmd_down ;;
    ps)    cmd_ps ;;
    ""|-h|--help|help) usage ;;
    *) echo "Unknown command: $action"; usage; exit 1 ;;
  esac
}

main "$@"

