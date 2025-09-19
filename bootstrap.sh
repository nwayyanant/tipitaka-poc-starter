#!/usr/bin/env bash
# bootstrap.sh — one-click helpers for Weaviate + Embedding Service + ETL pipeline
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="dev"
# Accept --prod as 2nd arg or 1st/any arg safely
for arg in "$@"; do
  if [[ "$arg" == "--prod" ]]; then
    MODE="prod"
  fi
done

COMPOSE_FILE="docker-compose.yml"
if [[ "$MODE" == "prod" ]]; then
  COMPOSE_FILE="docker-compose.prod.yml"
fi

# Detect docker compose v2 vs v1
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose -f $COMPOSE_FILE"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose -f $COMPOSE_FILE"
else
  echo "❌ docker compose not found" >&2
  exit 1
fi

# Default ports
WEAVIATE_HOST_PORT="${WEAVIATE_HOST_PORT:-8081}"
WEAVIATE_GRPC_HOST_PORT="${WEAVIATE_GRPC_HOST_PORT:-50052}"
EMBEDDING_HOST_PORT="${EMBEDDING_HOST_PORT:-8001}"

usage() {
  cat <<'EOF'
Usage: ./bootstrap.sh {setup|up|build|load|logs|down|ps} [--prod]

Options:
  --prod : use docker-compose.prod.yml (no volumes, baked-in data/code)

Commands:
  setup  : up → build → load (one-click)
  up     : start Weaviate + Embedding Service (and deps) in background
  build  : build ETL + Embedding Service images
  load   : run ETL pipeline (schema + CSV + vectors + sanity search)
  logs   : follow logs (weaviate + embedding + etl)
  down   : stop and remove containers/volumes (CAREFUL)
  ps     : show running containers for this project

Env (optional):
  WEAVIATE_HOST_PORT       (default: 8081)
  WEAVIATE_GRPC_HOST_PORT  (default: 50052)
  EMBEDDING_HOST_PORT      (default: 8001)
EOF
}

# ---- helpers ---------------------------------------------------------------

port_in_use() {
  # Cross-platform-ish port check: prefers ss/lsof; falls back to netstat (Windows)
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}$"
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP -sTCP:LISTEN -P 2>/dev/null | awk '{print $9}' | grep -qE "[:.]${port}$"
  else
    # Windows Git Bash fallback
    netstat -ano 2>/dev/null | tr -d '\r' | grep -E "LISTEN|LISTENING" | grep -q ":${port} "
  fi
}

check_ports() {
  for p in "$WEAVIATE_HOST_PORT" "$WEAVIATE_GRPC_HOST_PORT" "$EMBEDDING_HOST_PORT"; do
    if port_in_use "$p"; then
      echo "⚠️  Port ${p} looks in use on host. If compose fails, edit docker-compose*.yml to map a free port."
    fi
  done
}

wait_for_weaviate() {
  local url="http://localhost:${WEAVIATE_HOST_PORT}/v1/.well-known/ready"
  local max_wait="${WAIT_MAX_SEC:-120}"
  local waited=0
  local delay=2

  echo "⏳ Waiting for Weaviate on $url (timeout ${max_wait}s)…"
  until curl -fsSL "$url" >/dev/null 2>&1; do
    sleep "$delay"
    waited=$((waited+delay))
    if [ "$waited" -ge "$max_wait" ]; then
      echo "❌ Timeout: Weaviate not ready after ${max_wait}s" >&2
      exit 1
    fi
    if [ "$delay" -lt 10 ]; then
      delay=$((delay*2))
    fi
  done
  echo "✅ Weaviate is ready after ${waited}s."
}

wait_for_embedding() {
  local url="http://localhost:${EMBEDDING_HOST_PORT}/health"
  local max_wait="${WAIT_MAX_SEC:-120}"
  local waited=0
  local delay=2

  echo "⏳ Waiting for Embedding Service on $url (timeout ${max_wait}s)…"
  until curl -fsSL "$url" >/dev/null 2>&1; do
    sleep "$delay"
    waited=$((waited+delay))
    if [ "$waited" -ge "$max_wait" ]; then
      echo "❌ Timeout: Embedding Service not ready after ${max_wait}s" >&2
      exit 1
    fi
    if [ "$delay" -lt 10 ]; then
      delay=$((delay*2))
    fi
  done
  echo "✅ Embedding Service is ready after ${waited}s."
}

# ---- commands -------------------------------------------------------------

cmd_up() {
  check_ports
  echo "🚀 Starting services (weaviate + embedding)…"
  (cd "$PROJECT_ROOT" && $COMPOSE up -d --remove-orphans weaviate embedding-service)
  echo "✅ Services should be coming up."
  echo "   Weaviate GraphQL: http://localhost:${WEAVIATE_HOST_PORT}/v1/graphql"
  echo "   Embedding API    : http://localhost:${EMBEDDING_HOST_PORT}/embed"
}

cmd_build() {
  echo "🔧 Building ETL + Embedding Service images…"
  (cd "$PROJECT_ROOT" && $COMPOSE build etl embedding-service)
  echo "✅ Images built."
}

cmd_load() {
  echo "📦 Running ETL pipeline (schema + CSV + vectors + sanity)…"
  wait_for_weaviate
  wait_for_embedding
  (cd "$PROJECT_ROOT" && $COMPOSE run --rm etl)
  echo "✅ Data load finished."
}

cmd_logs() {
  echo "🪵 Tailing logs (Ctrl+C to stop)…"
  (cd "$PROJECT_ROOT" && $COMPOSE logs -f weaviate embedding-service etl || true)
}

cmd_down() {
  echo "🧹 Stopping and removing containers/volumes…"
  (cd "$PROJECT_ROOT" && $COMPOSE down -v)
  echo "✅ Done."
}

cmd_ps() {
  (cd "$PROJECT_ROOT" && $COMPOSE ps)
}

# ---- dispatcher -----------------------------------------------------------

main() {
  local cmd="${1:-}"
  # strip --prod if it was given as first argument
  if [[ "$cmd" == "--prod" ]]; then
    shift || true
    cmd="${1:-}"
  fi

  case "$cmd" in
    setup) cmd_up; cmd_build; cmd_load ;;
    up)    cmd_up ;;
    build) cmd_build ;;
    load)  cmd_load ;;
    logs)  cmd_logs ;;
    down)  cmd_down ;;
    ps)    cmd_ps ;;
    -h|--help|"") usage ;;
    *) echo "❌ Unknown command: $cmd"; usage; exit 1 ;;
  esac
}

main "$@"
