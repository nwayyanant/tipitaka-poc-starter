"""ETL configuration loader.


Loads environment variables from a .env file (if present) and exposes
typed configuration values to be consumed by the rest of the ETL package.
"""
from dotenv import load_dotenv
import os
from typing import Optional, Dict, Any


load_dotenv()




def env_bool(name: str, default: bool = False) -> bool:
val = os.getenv(name)
if val is None:
return default
return val.strip().lower() in {"1", "true", "yes", "y", "on"}




# ---------- Postgres (reserved for future) ----------
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tipitaka")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")


# ---------- Weaviate ----------
WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
CLASS_NAME: str = os.getenv("CLASS_NAME", "TipitakaChunk")
HF_MODEL_NAME: str = os.getenv("HF_MODEL_NAME", "sentence-transformers/LaBSE")
HUGGINGFACE_HUB_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_HUB_TOKEN")


# ---------- Data file paths ----------
CSV_CHUNKS: str = os.getenv("CSV_CHUNKS", "data/chunk.csv")
CSV_WINDOWS: str = os.getenv("CSV_WINDOWS", "data/windows.csv")
TEXT_COLUMN: str = os.getenv("TEXT_COLUMN", "pali_text")
WINDOW_COLUMN: str = os.getenv("WINDOW_COLUMN", "window_text")


# ---------- ETL runtime behavior ----------
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "200"))
DROP_AND_RECREATE: bool = env_bool("DROP_AND_RECREATE", False)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")




def as_dict() -> Dict[str, Any]:
return {
"WEAVIATE_URL": WEAVIATE_URL,
"CLASS_NAME": CLASS_NAME,
"HF_MODEL_NAME": HF_MODEL_NAME,
"CSV_CHUNKS": CSV_CHUNKS,
"CSV_WINDOWS": CSV_WINDOWS,
"BATCH_SIZE": BATCH_SIZE,
"DROP_AND_RECREATE": DROP_AND_RECREATE,
}




def summary() -> None:
print("ETL configuration summary:")
for k, v in as_dict().items():
print(f" {k}: {v}")
