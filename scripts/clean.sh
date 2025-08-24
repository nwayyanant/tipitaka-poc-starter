#!/usr/bin/env bash
set -euo pipefail


echo "Stopping and removing volumes..."
docker compose down -v