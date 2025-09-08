# Tipitaka POC Starter 

## Prerequisites

* Docker Desktop (Mac/Windows) or Docker + Docker Compose (Linux)
* Python 3.10+ if running scripts locally outside Docker
* Git Bash for cloning the repository

## Quick Start

Start Git Bash to run following steps 

1. **Clone the repo:**
   ```bash
   git clone https://github.com/nwayyanant/tipitaka-poc-starter.git
   ```


2. **Get latest source** (if needed)
	```bash
	./get_latest.sh
	```

3. **Reset Docker** (if needed)
	```bash
	./docker_reset.sh
	```

4. **Start Weaviate container**
	```bash
	./bootstrap.sh setup
	```

5. **Build ETL container** (if needed)
	```bash
	./bootstrap.sh build
	```

6. **Run ETL pipeline**

   ```bash
   ./bootstrap.sh load
   ```

   This will:

   * Create/reset schema in Weaviate
   * Load CSVs
   * Vectorize 
   * Ingest data into Weaviate


7. **Check Weaviate Schema** (it should return json. If it hangs or fails → service might not be ready or ports are misconfigured.)
	```bash
	curl -s http://localhost:8081/v1/schema
	```


8. **Check Container Status** (optional)
	```bash
	docker compose ps
	```

9. **Check data in Weaviate** (optional)
	```bash 
	curl -s -X POST http://localhost:8081/v1/graphql -H "Content-Type: application/json" -d "{\"query\":\"{ Aggregate { Chunk { meta { count } } } }\"}"
	```
	
10. **Search Data and output result to CSV** 

	usage: search_and_save.py
			--collection {Window, Sentence, Subchunk, Chunk}
    		[--mode {bm25,hybrid,vector}]
    		--query QUERY
    		[--k K]
    		[--alpha ALPHA]

    
	example #1
    ```bash
	docker compose run --rm etl python etl/app/search_and_save.py --collection Window --mode hybrid --alpha 0.5 --query "mettā" --k 5
	```
	
	example #2
    ```bash
	docker compose run --rm etl python etl/app/search_and_save.py --collection Sentence --mode vector --query "mettā" --k 10
	```
	




