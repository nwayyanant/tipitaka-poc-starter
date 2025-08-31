FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget curl build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Pre-cache LaBSE model
ENV TRANSFORMERS_CACHE=/app/.cache
ENV HF_HOME=/app/.cache
ENV TORCH_HOME=/app/.cache
ENV DEVICE=cpu
ENV MODEL_NAME=sentence-transformers/LaBSE

RUN python - <<'PY'
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/LaBSE", device="cpu")
model.encode(["warmup"], normalize_embeddings=False)
print("LaBSE preloaded")
PY

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
