from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

# Load LaBSE once at startup
MODEL_NAME = "sentence-transformers/LaBSE"
print(f"Loading model {MODEL_NAME} ...")
model = SentenceTransformer(MODEL_NAME)
print("Model loaded ✅")

# FastAPI app
app = FastAPI()

class EmbedRequest(BaseModel):
    text: str

@app.post("/embed")
def embed(req: EmbedRequest):
    vec = model.encode(req.text).tolist()
    return {"vector": vec}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
