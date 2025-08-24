"""
embedder.py
-----------
Handles vectorization and ingestion of text data into Weaviate.
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.util import get_valid_uuid
import os

from etl.config import Config
from etl.data_loader import load_chunk_csv, load_windows_csv

# Optional: for custom embeddings (sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class Embedder:
    def __init__(self, config: Config):
        self.config = config

        # Connect to Weaviate
        self.client = weaviate.Client(
            url=self.config.WEAVIATE_URL,
            auth_client_secret=Auth.api_key(self.config.WEAVIATE_API_KEY)
            if self.config.WEAVIATE_API_KEY else None
        )

        # If using custom model
        if self.config.EMBEDDING_MODEL != "weaviate":
            if not SentenceTransformer:
                raise ImportError(
                    "sentence-transformers is required for custom embeddings. "
                    "Please install it in requirements.txt."
                )
            self.model = SentenceTransformer(self.config.EMBEDDING_MODEL)
        else:
            self.model = None

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with either Weaviate built-in or local model."""
        if self.model:  # custom embeddings
            return self.model.encode(texts, show_progress_bar=True).tolist()
        else:
            # Let Weaviate handle embeddings (e.g., text2vec-openai module)
            return None

    def ingest_csv(self, use_windows: bool = False, limit: int | None = None):
        """Ingest CSV rows into Weaviate, vectorizing if needed."""
        if use_windows:
            df = load_windows_csv(self.config)
        else:
            df = load_chunk_csv(self.config)

        if limit:
            df = df.head(limit)

        print(f"Loaded {len(df)} rows from {'windows.csv' if use_windows else 'chunk.csv'}")

        # Choose text field depending on CSV
        text_field = "pali_text" if "pali_text" in df.columns else "window_text"

        texts = df[text_field].tolist()

        vectors = self._embed_texts(texts) if self.model else [None] * len(texts)

        with self.client.batch as batch:
            batch.batch_size = 64
            for i, row in df.iterrows():
                properties = row.to_dict()
                uuid = get_valid_uuid(str(row.get("chunk_id", row.get("window_id", i))))

                batch.add_data_object(
                    data_object=properties,
                    class_name=self.config.CLASS_NAME,
                    uuid=uuid,
                    vector=vectors[i] if vectors and vectors[i] is not None else None,
                )

        print(f"✅ Successfully ingested {len(df)} objects into Weaviate.")


if __name__ == "__main__":
    cfg = Config()
    embedder = Embedder(cfg)

    # Example: ingest 100 chunks
    embedder.ingest_csv(use_windows=False, limit=100)
