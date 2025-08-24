"""
load_weaviate.py
----------------
Orchestrates the full ETL pipeline:
1. Create or reset schema in Weaviate
2. Load CSVs
3. Embed + Ingest into Weaviate
"""

from etl.config import Config
from etl.weaviate_schema import create_schema
from etl.embedder import Embedder


def main():
    cfg = Config()

    print("🚀 Starting ETL pipeline...")

    # Step 1: Create or reset schema
    create_schema(cfg)

    # Step 2: Ingest data
    embedder = Embedder(cfg)

    # Ingest both chunk.csv and windows.csv
    print("📥 Ingesting chunk.csv...")
    embedder.ingest_csv(use_windows=False, limit=None)

    print("📥 Ingesting windows.csv...")
    embedder.ingest_csv(use_windows=True, limit=None)

    print("✅ ETL pipeline finished successfully!")


if __name__ == "__main__":
    main()
