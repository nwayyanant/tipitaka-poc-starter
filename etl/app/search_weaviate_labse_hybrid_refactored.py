# search_weaviate_labse_hybrid_refactored.py
import argparse
import os
import csv
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

import numpy as np
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams


# --------------------------
# Configuration
# --------------------------
DEFAULT_MODEL = os.getenv("MODEL_NAME", "sentence-transformers/LaBSE")
LABSE_DEVICE = os.getenv("LABSE_DEVICE")  # 'cpu' | 'cuda' | 'mps' | None

COLLECTION_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "Window": {
        "props": ["window_id", "text", "chunk_id", "path", "h1", "h2", "h3", "h4", "h5", "h6"],
        "text_key": "text",
        "id_format": lambda p: f"[window] {p.get('window_id','')} | chunk={p.get('chunk_id','')}",
        "suffix": lambda p: " | Headings: " + " > ".join(
            x for x in [p.get("h1"), p.get("h2"), p.get("h3"),
                        p.get("h4"), p.get("h5"), p.get("h6")] if x
        ) or "",
    },
    "Sentence": {
        "props": ["sentence_id", "sentence_text", "chunk_id", "path", "h1", "h2", "h3", "h4", "h5", "h6"],
        "text_key": "sentence_text",
        "id_format": lambda p: f"[sentence] {p.get('sentence_id','')} | chunk={p.get('chunk_id','')}",
        "suffix": lambda p: "",
    },
    "Subchunk": {
        "props": ["subchunk_id", "subchunk_text", "chunk_id"],
        "text_key": "subchunk_text",
        "id_format": lambda p: f"[subchunk] {p.get('subchunk_id','')} | chunk={p.get('chunk_id','')}",
        "suffix": lambda p: "",
    },
    "Chunk": {
        "props": ["chunk_id", "chunk_text"],
        "text_key": "chunk_text",
        "id_format": lambda p: f"[chunk] {p.get('chunk_id','')}",
        "suffix": lambda p: "",
    },
}


# --------------------------
# Model wrapper
# --------------------------
class LabseEncoder:
    def __init__(self, model_name: str, device: str | None = None):
        from sentence_transformers import SentenceTransformer
        import torch

        if not device:
            device = (
                "cuda" if torch.cuda.is_available()
                else "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
                else "cpu"
            )
        self.model = SentenceTransformer(model_name, device=device)
        logging.info(f"Loaded model {model_name} on {device}")

    def encode(self, text: str) -> np.ndarray:
        vec = self.model.encode([text], normalize_embeddings=False, convert_to_numpy=True)
        return vec.astype(np.float32)[0]


# --------------------------
# Utility functions
# --------------------------
def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--url", default=os.getenv("WEAVIATE_URL", "http://localhost:8081"),
                        help="Weaviate REST URL")
    parser.add_argument("--grpc-port", type=int, default=int(os.getenv("WEAVIATE_GRPC_PORT", 50052)),
                        help="Weaviate gRPC port")
    parser.add_argument("--collection", required=True, help="Name of the collection / class")
    parser.add_argument("--mode", choices=["bm25", "hybrid", "vector"], default="bm25",
                        help="Search mode (default: bm25)")
    parser.add_argument("--query", required=True, help="Search query text")
    parser.add_argument("--k", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="hybrid alpha (0..1), higher favors vector")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help="Embedding model for vector search")
    parser.add_argument("--output-dir", type=str, default="./weaviate-result",
                        help="Directory to save CSV results")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def get_client(url: str, grpc_port: int) -> WeaviateClient:
    cp = ConnectionParams.from_url(url, grpc_port=grpc_port)
    client = WeaviateClient(cp)
    client.connect()
    return client


def short_text(s: str, n: int = 180) -> str:
    s = s or ""
    s = " ".join(s.split())
    return s[:n] + ("..." if len(s) > n else "")


# --------------------------
# Core search / output
# --------------------------
def search_collection(client: WeaviateClient, args, encoder: LabseEncoder):
    schema = COLLECTION_SCHEMAS.get(args.collection)
    if not schema:
        raise ValueError(f"Unsupported collection: {args.collection}")

    coll = client.collections.get(args.collection)

    if args.mode == "vector":
        qvec = encoder.encode(args.query)
        return coll.query.near_vector(
            near_vector=qvec, limit=args.k, return_properties=schema["props"]
        )
    elif args.mode == "hybrid":
        qvec = encoder.encode(args.query)
        return coll.query.hybrid(
            query=args.query, vector=qvec, alpha=args.alpha,
            limit=args.k, return_properties=schema["props"]
        )
    else:  # bm25
        return coll.query.bm25(
            query=args.query, limit=args.k, return_properties=schema["props"]
        )


def save_to_csv(results, args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"weaviate_results_{timestamp}.csv"

    schema = COLLECTION_SCHEMAS[args.collection]
    fieldnames = ["rank", "collection", "query", "mode", "alpha", "score"] + schema["props"]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, obj in enumerate(results.objects or [], start=1):
            score = getattr(obj.metadata, "score", None)
            score_str = f"{score:.4f}" if score is not None else "N/A"

            row = {
                "rank": i,
                "collection": args.collection,
                "query": args.query,
                "mode": args.mode,
                "alpha": args.alpha if args.mode == "hybrid" else "N/A",
                "score": score_str,
            }

            for key in schema["props"]:
                row[key] = str(obj.properties.get(key, "")) if obj.properties else ""

            writer.writerow(row)

    logging.info(f"Results saved to: {filename}")
    return filename


def print_results(results, args):
    schema = COLLECTION_SCHEMAS[args.collection]

    for i, o in enumerate(results.objects or [], start=1):
        p = o.properties or {}
        score = getattr(o.metadata, "score", None)
        score_str = f"{score:.4f}" if score is not None else "N/A"

        idx = schema["id_format"](p)
        suffix = schema["suffix"](p)
        text = p.get(schema["text_key"], "")

        print(f"{i:>2}. {idx}{suffix} (score: {score_str})")
        print(f"    {short_text(text)}")


# --------------------------
# Entry point
# --------------------------
def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))

    logging.info(f"🔗 Connecting to Weaviate at {args.url} (gRPC {args.grpc_port})")

    try:
        client = get_client(args.url, args.grpc_port)
    except Exception as e:
        raise SystemExit(f"❌ Could not connect to Weaviate: {e}")

    try:
        encoder = LabseEncoder(args.model, LABSE_DEVICE)
        results = search_collection(client, args, encoder)

        print(f"[results] {len(results.objects)} objects")
        save_to_csv(results, args)
        print_results(results, args)
    finally:
        client.close()


if __name__ == "__main__":
    main()
