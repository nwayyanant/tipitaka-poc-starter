from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import Literal, List, Optional
from utils import get_client, encode_query_remote, pick_return_props

# ------------------------------------------------------
# Config (use env vars for flexibility in production)
# ------------------------------------------------------

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT", 50051))
COLLECTION = os.getenv("WEAVIATE_COLLECTION", "Chunk")

# ------------------------------------------------------
# FastAPI app
# ------------------------------------------------------

app = FastAPI(title="Search Service", version="1.0")

# Pydantic request schema
class SearchRequest(BaseModel):
    collection: str
    query: str
    mode: Literal["bm25", "vector", "hybrid"] = "bm25"
    k: int = 5
    alpha: float = 0.5 # only for hybrid

# Response schema
class SearchResult(BaseModel):
    text: str
    score: Optional[float] = None
    metadata: dict


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Useful for bootstrap.sh readiness checks.
    """
    try:
        client = get_client(WEAVIATE_URL, WEAVIATE_GRPC_PORT)
        # simple ping (doesn't throw if available)
        client.close()
        return {"status": "ok", "service": "search"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {e}")


@app.post("/search")
async def search(req: SearchRequest)-> List[SearchResult]:
    results = []
    try:
        client = get_client(WEAVIATE_URL, WEAVIATE_GRPC_PORT)
        coll = client.collections.get(req.collection)
        props = pick_return_props(req.collection)

        if req.mode == "vector":
            qvec = encode_query_remote(req.query)
            res = coll.query.near_vector(near_vector=qvec, limit=req.k, return_properties=props)
        elif req.mode == "hybrid":
            qvec = encode_query_remote(req.query)
            res = coll.query.hybrid(query=req.query, vector=qvec, alpha=req.alpha, limit=req.k, return_properties=props)
        else:
            res = coll.query.bm25(query=req.query, limit=req.k, return_properties=props)

        for o in res.objects or []:
            p = o.properties or {}
            score = getattr(o.metadata, "score", None)
            results.append(SearchResult(
                text=p.get("text") or p.get("sentence_text") or p.get("subchunk_text") or p.get("chunk_text", ""),
                score=score,
                metadata=p,
            ))
         
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()
    
    return results

# ✅ Dev mode: can run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
