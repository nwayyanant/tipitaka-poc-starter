# search_weaviate_labse_hybridfix.py
import argparse
import os
import csv
from typing import List
import numpy as np
from datetime import datetime

from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams

DEFAULT_MODEL = os.getenv("MODEL_NAME", "sentence-transformers/LaBSE")
LABSE_DEVICE = os.getenv("LABSE_DEVICE")  # 'cpu' | 'cuda' | 'mps' | None

_model = None  # lazy singleton


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        default=os.getenv("WEAVIATE_URL", "http://localhost:8081"),
        help="Weaviate REST URL (default: from WEAVIATE_URL env or localhost:8081)"
    )
    parser.add_argument(
        "--grpc-port",
        type=int,
        default=int(os.getenv("WEAVIATE_GRPC_PORT", 50052)),
        help="Weaviate gRPC port (default: from WEAVIATE_GRPC_PORT env or 50052)"
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="Name of the collection / class"
    )
    parser.add_argument(
        "--mode",
        choices=["bm25", "hybrid", "vector"],
        default="bm25",
        help="Search mode (default: bm25)"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search query text"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--alpha", 
        type=float, 
        default=0.5, 
        help="hybrid alpha (0..1) higher favors vector"
    )
    parser.add_argument(
    "--model",
    type=str,
    default="sentence-transformers/LaBSE",
    help="Embedding model to use for vector search"
    )

    return parser.parse_args()


def get_client(url: str, grpc_port: int) -> WeaviateClient:
    cp = ConnectionParams.from_url(url, grpc_port=grpc_port)
    client = WeaviateClient(cp)
    client.connect()
    return client


def _load_model(model_name: str):
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        try:
            import torch
            if LABSE_DEVICE:
                device = LABSE_DEVICE
            else:
                device = "cuda" if torch.cuda.is_available() else (
                    "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu"
                )
        except Exception:
            device = LABSE_DEVICE or "cpu"
        _model = SentenceTransformer(model_name, device=device)
        return _model
    except ModuleNotFoundError as e:
        raise SystemExit(
            "ERROR: sentence-transformers not found in this environment.\n"
            "Inside Docker, ensure your Dockerfile runs: pip install -r requirements.txt"
        ) from e


def encode_query_labse(text: str, model_name: str) -> np.ndarray:
    model = _load_model(model_name)
    vec = model.encode([text], normalize_embeddings=False, convert_to_numpy=True)
    return vec.astype(np.float32)[0]


def pick_return_props(coll_name: str) -> List[str]:
    if coll_name == "Window":
        return ["window_id", "text", "chunk_id", "path", "h1", "h2", "h3", "h4", "h5", "h6"]
    if coll_name == "Sentence":
        return ["sentence_id", "sentence_text", "chunk_id", "path", "h1", "h2", "h3", "h4", "h5", "h6"]
    if coll_name == "Subchunk":
        return ["subchunk_id", "subchunk_text", "chunk_id"]
    if coll_name == "Chunk":
        return ["chunk_id", "chunk_text"]
    return []


def short_text(s: str, n: int = 180) -> str:
    s = s or ""
    s = " ".join(s.split())
    return s[:n] + ("..." if len(s) > n else "")


def save_to_csv(results, collection_name, query, mode, alpha, output_dir="/app/weaviate-result"):
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/weaviate_results_{timestamp}.csv"
    
    # Define CSV fieldnames
    fieldnames = ["rank", "collection", "query", "mode", "alpha", "score"]
    
    # Add collection-specific fields
    if collection_name == "Window":
        fieldnames.extend(["window_id", "text", "chunk_id", "path", "h1", "h2", "h3", "h4", "h5", "h6"])
    elif collection_name == "Sentence":
        fieldnames.extend(["sentence_id", "sentence_text", "chunk_id", "path", "h1", "h2", "h3", "h4", "h5", "h6"])
    elif collection_name == "Subchunk":
        fieldnames.extend(["subchunk_id", "subchunk_text", "chunk_id"])
    elif collection_name == "Chunk":
        fieldnames.extend(["chunk_id", "chunk_text"])
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, obj in enumerate(results.objects or [], start=1):
            # Handle score safely
            score = getattr(obj.metadata, 'score', None) if hasattr(obj, 'metadata') else None
            score_str = f"{score:.4f}" if score is not None else "N/A"
            
            row = {
                "rank": i,
                "collection": collection_name,
                "query": query,
                "mode": mode,
                "alpha": alpha if mode == "hybrid" else "N/A",
                "score": score_str
            }
            
            # Add properties
            properties = obj.properties or {}
            for key in properties:
                if key in fieldnames:
                    row[key] = str(properties.get(key, ""))
            
            writer.writerow(row)
    
    print(f"Results saved to: {filename}")
    return filename


def main():
    args = parse_args()
    print(f"🔗 Connecting to Weaviate at {args.url} (gRPC {args.grpc_port})")
    
    client = get_client(args.url, args.grpc_port)
    try:
        coll = client.collections.get(args.collection)
        props = pick_return_props(args.collection)

        if args.mode == "vector":
            qvec = encode_query_labse(args.query, args.model)
            res = coll.query.near_vector(
                near_vector=qvec,
                limit=args.k,
                return_properties=props,
            )
        elif args.mode == "hybrid":
            qvec = encode_query_labse(args.query, args.model)
            res = coll.query.hybrid(
                query=args.query,
                vector=qvec,
                alpha=args.alpha,
                limit=args.k,
                return_properties=props,
            )
        else:  # bm25
            res = coll.query.bm25(
                query=args.query,
                limit=args.k,
                return_properties=props,
            )

        print(f"[results] {len(res.objects)} objects")
        
        # Save results to CSV
        csv_file = save_to_csv(res, args.collection, args.query, args.mode, args.alpha)
        
        # Print results to console
        for i, o in enumerate(res.objects or [], start=1):
            p = o.properties or {}
            kind = args.collection.lower()
            
            # Handle score safely
            score = getattr(o.metadata, 'score', None) if hasattr(o, 'metadata') else None
            score_str = f"{score:.4f}" if score is not None else "N/A"
            
            if args.collection == "Window":
                idx = f"[{kind}] {p.get('window_id','')} | chunk={p.get('chunk_id','')}"
                text = p.get("text", "")
                trail = " > ".join(x for x in [p.get("h1"), p.get("h2"), p.get("h3"), p.get("h4"), p.get("h5"), p.get("h6")] if x)
                suffix = f" | Headings: {trail}" if trail else ""
            elif args.collection == "Sentence":
                idx = f"[{kind}] {p.get('sentence_id','')} | chunk={p.get('chunk_id','')}"
                text = p.get("sentence_text", "")
                suffix = ""
            elif args.collection == "Subchunk":
                idx = f"[{kind}] {p.get('subchunk_id','')} | chunk={p.get('chunk_id','')}"
                text = p.get("subchunk_text", "")
                suffix = ""
            else:
                idx = f"[{kind}] {p.get('chunk_id','')}"
                text = p.get("chunk_text", "")
                suffix = ""

            print(f"{i:>2}. {idx}{suffix} (score: {score_str})")
            print(f"    {short_text(text)}")
            
    finally:
        client.close()


if __name__ == "__main__":
    main()