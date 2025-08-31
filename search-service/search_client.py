import os
import numpy as np
import httpx
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from typing import List

EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://embedding:8000/encode")

class SearchClient:
    def __init__(self, weaviate_url=None, grpc_port=50051):
        self.weaviate_url = weaviate_url or os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        self.grpc_port = grpc_port
        cp = ConnectionParams.from_url(self.weaviate_url, grpc_port=self.grpc_port)
        self.client = WeaviateClient(cp)
        self.client.connect()
        self.http = httpx.Client(timeout=15)

    def encode_query(self, text: str) -> np.ndarray:
        resp = self.http.post(EMBEDDING_URL, json={"text": text})
        resp.raise_for_status()
        vec = resp.json().get("vector")
        if vec is None:
            raise RuntimeError("Embedding service returned no vector")
        return np.array(vec, dtype=np.float32)

    def search_vector(self, collection: str, query_vec: np.ndarray, top_k=5, hybrid_query=None, alpha=0.5):
        coll = self.client.collections.get(collection)
        props = [p["name"] for p in coll.properties]
        if hybrid_query:
            res = coll.query.hybrid(query=hybrid_query, vector=query_vec, alpha=alpha, limit=top_k, return_properties=props)
        else:
            res = coll.query.near_vector(near_vector=query_vec, limit=top_k, return_properties=props)
        return res
