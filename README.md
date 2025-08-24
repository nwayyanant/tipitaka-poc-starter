# Tipitaka Semantic Search PoC

This repository contains a proof-of-concept pipeline for importing Tipitaka Pali texts 
into (Postgres and) Weaviate with vector embeddings.

## Quick Start

1. Clone the repo:

   git clone https://github.com/your-org/tipitaka-poc.git
   cd tipitaka-poc

	
2. Copy environment file :
	cp .env.example .env
	

3. Add your data files under data/:
	example: chunk.csv, windows.csv # these file can be manually download from google drive


4. Start everything:
	./scripts/start.sh



5. Repo Structure 
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
│ ├── pipeline.py
│ ├── weaviate_schema.py
│ ├── load_postgres.py
│ ├── load_weaviate.py
│ └── utils.py
└── scripts/
├── start.sh
├── reseed.sh
├── restart.sh
├── stop.sh
└── clean.sh

Put your CSVs into data/ before running. Copy .env.example → .env and adjust if needed.