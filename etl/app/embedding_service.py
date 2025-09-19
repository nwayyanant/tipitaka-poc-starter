from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/LaBSE"
print(f"Loading model {MODEL_NAME} ...")
model = SentenceTransformer(MODEL_NAME)
print("Model loaded ✅")

app = FastAPI()

class EmbedRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}

@app.post("/embed")
def embed(req: EmbedRequest):
    vec = model.encode(req.text).tolist()
    return {"vector": vec}
