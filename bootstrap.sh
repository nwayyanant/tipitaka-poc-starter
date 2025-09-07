#!/usr/bin/env bash
# bootstrap.sh — one-click helpers for Weaviate + ETL pipeline
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# At top
MODE="dev"
if [[ "${2:-}" == "--prod" ]]; then
  MODE="prod"
  shift
fi

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



# Default ports — keep consistent with docker-compose.yml
WEAVIATE_HOST_PORT="${WEAVIATE_HOST_PORT:-8081}"
WEAVIATE_GRPC_HOST_PORT="${WEAVIATE_GRPC_HOST_PORT:-50052}"



usage() {
  cat <<EOF
Usage: ./bootstrap.sh {setup|up|build|load|logs|down|ps} [--prod]

Options:
  --prod : use docker-compose.prod.yml (no volumes, baked-in data/code)

  setup  : up → build → load (one-click)
  up     : start Weaviate (and deps) in background
  build  : build ETL image
  load   : run ETL pipeline (schema + CSV + vectors + sanity search)
  logs   : follow logs (weaviate + etl)
  down   : stop and remove containers/volumes (CAREFUL)
  ps     : show running containers for this project

Env (optional):
  WEAVIATE_HOST_PORT       (default: 8081)
  WEAVIATE_GRPC_HOST_PORT  (default: 50052)
EOF
}
wait_for_weaviate() {
  local url="http://localhost:${WEAVIATE_HOST_PORT}/v1/.well-known/ready"
  local max_wait="${WAIT_MAX_SEC:-300}" # bump default to 5min
  local waited=0
  local delay=2

  echo "⏳ Waiting for Weaviate to be ready on $url (timeout ${max_wait}s)…"

  until curl -fsSL "$url" >/dev/null 2>&1; do
    sleep "$delay"
    waited=$((waited+delay))
    if [ "$waited" -ge "$max_wait" ]; then
      echo "❌ Timeout: Weaviate not ready after ${max_wait}s" >&2
      exit 1
    fi

    # exponential backoff up to 10s max
    if [ "$delay" -lt 10 ]; then
      delay=$((delay*2))
    fi
  done

  echo "✅ Weaviate is ready after ${waited}s."
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
  for p in "$WEAVIATE_HOST_PORT" "$WEAVIATE_GRPC_HOST_PORT"; do
    if port_in_use "$p"; then
      echo "⚠️  Port ${p} looks in use on host. If compose fails, edit docker-compose.yml to map a free port."
    fi
  done
}

cmd_up() {
  check_ports
  echo "🚀 Starting services (weaviate)…"
  (cd "$PROJECT_ROOT" && $COMPOSE up -d --remove-orphans weaviate)
  echo "✅ Weaviate should be coming up."
  echo "   Try: http://localhost:${WEAVIATE_HOST_PORT}/v1/graphql"
  echo "🌐 Weaviate REST will be available at: http://localhost:${WEAVIATE_HOST_PORT}/v1/graphql"
  echo "🌐 Weaviate gRPC will be available at: localhost:${WEAVIATE_GRPC_HOST_PORT}"

}

cmd_build() {
  echo "🔧 Building ETL image…"
  (cd "$PROJECT_ROOT" && $COMPOSE build etl)
  echo "✅ ETL image built."
}

cmd_load() {
  echo "📦 Running ETL pipeline (schema + CSV + vectors + sanity)…"
  wait_for_weaviate
  (cd "$PROJECT_ROOT" && $COMPOSE run --rm etl)
  echo "✅ Data load finished."
}


cmd_logs() {
  echo "🪵 Tailing logs (Ctrl+C to stop)…"
  (cd "$PROJECT_ROOT" && $COMPOSE logs -f weaviate etl || true)
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
