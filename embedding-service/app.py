from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os
import numpy as np
from typing import List, Union

app = FastAPI(title="LaBSE Embedding Service")

DEVICE = os.getenv("DEVICE", "cpu")
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/LaBSE")

# Load model once at startup
print(f"[embedding] loading model {MODEL_NAME} on device={DEVICE}")
model = SentenceTransformer(MODEL_NAME, device=DEVICE)
print("[embedding] model loaded")

class EncodeOne(BaseModel):
    text: str

class EncodeMany(BaseModel):
    texts: List[str]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/encode")
async def encode(req: Union[EncodeOne, EncodeMany]):
    """
    Accepts single text or list of texts.
    Returns float32 numpy vectors.
    """
    if hasattr(req, 'text'):
        vec = model.encode([req.text], normalize_embeddings=False, convert_to_numpy=True)[0]
        return {"vector": vec.astype(np.float32).tolist()}
    elif hasattr(req, 'texts'):
        vecs = model.encode(req.texts, normalize_embeddings=False, convert_to_numpy=True)
        return {"vectors": [v.astype(np.float32).tolist() for v in vecs]}
    else:
        return {"error": "invalid request"}
