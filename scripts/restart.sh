#!/usr/bin/env bash
set -euo pipefail


echo "Restarting stack..."
docker compose down
./scripts/start.sh