import os
import pandas as pd
import weaviate
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from tqdm import tqdm

# Load .env vars
load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/LaBSE")

# Connect to Weaviate
client = weaviate.Client(WEAVIATE_URL)

# Load model
model = SentenceTransformer(MODEL_NAME)

# Example: load chunk.csv
df = pd.read_csv("data/chunk.csv")

# Vectorize a column (e.g., 'pali_text')
vectors = model.encode(df["pali_text"].tolist(), show_progress_bar=True)

# Add vectors to dataframe
df["vector"] = vectors.tolist()

# Push to Weaviate
for i, row in tqdm(df.iterrows(), total=len(df)):
    client.data_object.create(
        data_object={
            "text": row["pali_text"],
        },
        class_name="PaliChunk",
        vector=row["vector"],
        uuid=None  # let Weaviate assign UUID
    )

print("✅ Finished importing to Weaviate")
