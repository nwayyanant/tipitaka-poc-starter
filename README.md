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
   cd tipitaka-poc-starter
   ```


2. **Get latest source**
	```bash
	./get_latest.sh
	```

3. **Reset Docker** (To start from fresh)
	```bash
	./docker_reset.sh
	```

4. **Environment Setup**
	```bash
	./bootstrap.sh setup
	```


5. **Check Weaviate Schema** (Optional, it should return json. If it hangs or fails → service might not be ready or ports are misconfigured.)
	```bash
	curl -s http://localhost:8090/v1/schema
	```


6. **Check Container Status** (Optional)
	```bash
	docker compose ps
	```

7. **check data inside chunk** (Not required, only if you interested)
	```bash 
	curl -s -X POST http://localhost:8090/v1/graphql -H "Content-Type: application/json" -d "{\"query\":\"{ Aggregate { Chunk { meta { count } } } }\"}"
	```
	
## Simple Search (TEST)
	
	1. **example #1** 
 
	```bash
	 python /workspace/etl/app/search_weaviate_labse_hybridfix.py --url http://weaviate:8080 --grpc-port 50051 --collection Window --mode hybrid --query mettā --k 5 --alpha 0.5
	```
	
	2. example #2 using search service - command line
 
	```bash
	docker compose run --rm search python cli.py --collection Window --mode hybrid --query "mettā" --k 10
	```
	
	```bash
	docker compose run --rm search python cli.py --collection Window --mode hybrid --query "puttā" --k 10
	```
	
	```bash
	docker compose run --rm search python cli.py --collection Window --mode hybrid --query "bhagavā" --k 10
	```
	 
 
	

##Change Log **20250922**
	
	Separation of concerns → embedding, search, ETL are independent.
	Scalable → can run multiple embedding replicas if queries grow.
	Slim images → only embedding has LaBSE baked in, search stays lightweight.
	Data persistence → Weaviate uses a named volume.
	Prod ready → Gunicorn workers auto-scale based on CPU cores.
	
	
	
## bootstrap.sh Usage Examples

	Dev mode (default)

	./bootstrap.sh up
	→ runs with override → hot reload.

	Prod mode

	./bootstrap.sh up --prod

	→ runs with prod file → optimized containers.
