#!/usr/bin/env bash
set -euo pipefail


# Optional: allow DROP via env var on the one-off run
DROP_AND_RECREATE=${DROP_AND_RECREATE:-false}


echo "Running ETL reseed (DROP_AND_RECREATE=${DROP_AND_RECREATE})..."
docker compose run --rm -e DROP_AND_RECREATE=${DROP_AND_RECREATE} etl