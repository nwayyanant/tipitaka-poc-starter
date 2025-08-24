# Tipitaka Semantic Search PoC

This repository contains a proof-of-concept pipeline for importing Tipitaka Pali texts 
into (Postgres and) Weaviate with vector embeddings.

## Quick Start

1. Clone the repo:

   git clone https://github.com/nwayyanant/tipitaka-poc-starter.git
   cd tipitaka-poc-starter

	
2. Copy environment file : Copy .env.example → .env and adjust if needed.
	cp .env.example .env
	

3. Add your data files under data/: Put your CSVs into data/ before running. 
	example: chunk.csv, windows.csv # these file can be manually download from google drive


4. Start everything:
	./scripts/start.sh


5. Repo Structure should be:
```
weaviate-poc-starter/
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
├── data/
	│ ├── chunk.csv # required (e.g., columns: chunk_id,pali_text,...)
	│ └── windows.csv # optional (e.g., columns: chunk_id,window_text,...)
├── etl/
	│ ├── Dockerfile
	│ ├── requirements.txt
	│ └── app/
	│ 	├── pipeline.py
	│ 	├── weaviate_schema.py
	│ 	├── load_postgres.py
	│ 	├── load_weaviate.py
	│ 	└── utils.py
└── scripts/
	├── start.sh
	├── reseed.sh
	├── restart.sh
	├── stop.sh
	└── clean.sh

```


# Tipitaka PoC Search System (modified version)

This repository contains a prototype pipeline for importing Tipitaka data into Weaviate for semantic search.
It includes Docker setup, Python ETL scripts, schema management, and optional embeddings.

---

## 📂 Repo Structure

```
├── data/                 # Place your CSV files here (chunk.csv, windows.csv)
├── docker-compose.yml    # Docker services for Weaviate and ETL
├── Dockerfile.etl        # Builds Python ETL container
├── etl/                  # Python ETL package
│   ├── __init__.py
│   ├── config.py         # Configuration loader (.env)
│   ├── data_loader.py    # CSV loader & cleaning
│   ├── embedder.py       # Vectorize & push to Weaviate
│   ├── weaviate_schema.py# Schema creation/reset
│   └── load_weaviate.py  # Orchestrator (schema + ingestion)
├── .env.example          # Example environment variables
├── Makefile              # Optional commands for quick setup
└── bootstrap.sh          # Cross-platform startup script
```

---

## ⚙️ Prerequisites

* Docker Desktop (Mac/Windows) or Docker + Docker Compose (Linux)
* Python 3.10+ if running scripts locally outside Docker
* Git for cloning the repository

Optional:

* `make` for running Makefile targets (Linux/Mac/WSL)

---

## 📝 Setup Steps

1. **Clone the repository**

   ```bash
   git clone <repo_url>
   cd <repo_folder>
   ```

2. **Copy environment file**

   ```bash
   cp .env.example .env
   # Edit .env to set your own configuration if needed
   ```

3. **Start Weaviate container**

   ```bash
   ./bootstrap.sh up
   # OR using Makefile: make up
   ```

4. **Build ETL container** (if needed)

   ```bash
   ./bootstrap.sh build
   # OR using Makefile: make build
   ```

5. **Run ETL pipeline**

   ```bash
   ./bootstrap.sh load
   # OR using Makefile: make load
   ```

   This will:

   * Create/reset schema in Weaviate
   * Load chunk.csv and windows.csv
   * Vectorize text (using Weaviate module or local model)
   * Ingest data into Weaviate

6. **View Weaviate Playground**
   Open in browser:

   ```
   http://localhost:8080
   ```

7. **Stop containers**

   ```bash
   ./bootstrap.sh down
   # OR using Makefile: make down
   ```

8. **Follow logs (optional)**

   ```bash
   ./bootstrap.sh logs
   # OR using Makefile: make logs
   ```

---

## 🛠️ Notes for Team

* Only `bootstrap.sh` or `Makefile` commands are needed.
* CSV files must follow the expected columns:

  * chunk.csv → at least `chunk_id` and `pali_text`
  * windows.csv → at least `window_id` and `window_text`
* Environment variables are read from `.env`
* Re-running `./bootstrap.sh load` will skip existing data if UUIDs match.

---

## 🏗️ Development Tips

* Add new CSVs or modify schema in `etl/weaviate_schema.py`.
* Extend vectorization in `etl/embedder.py` for custom models.
* Check data loading and cleaning in `etl/data_loader.py`.
* Use `config.py` to centralize all settings.

---

## ✅ Summary

This setup ensures that any team member can spin up a local instance, reset schema, and ingest data with **one simple command**. It’s reproducible, modular, and ready for PoC or internal testing.



