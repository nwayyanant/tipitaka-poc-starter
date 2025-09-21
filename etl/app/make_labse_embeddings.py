
import argparse
import csv
import os
import sys
from typing import List, Tuple

import requests
import numpy as np
import tqdm  # optional, for progress bar

EMBEDDING_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding:8000/embed-many")

def embed_batch(texts, batch_size=32, normalize=True):
    """
    Send a batch of texts to the embedding service.
    """
    vectors = []
    for i in tqdm.trange(0, len(texts), batch_size, desc="Embedding"):
        batch = texts[i:i+batch_size]
        resp = requests.post(
            EMBEDDING_URL,
            json={"texts": batch},  # <-- we'll extend embedding service to support lists
            timeout=60
        )
        resp.raise_for_status()
        vecs = np.array(resp.json()["vectors"], dtype=np.float32)
        if normalize:
            # L2 normalize
            norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10
            vecs = vecs / norms
        vectors.append(vecs)
    return np.vstack(vectors)


def read_pairs(csv_path: str, text_col: str, id_col: str) -> Tuple[List[str], List[str]]:
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if text_col not in reader.fieldnames or id_col not in reader.fieldnames:
            raise ValueError(f"Expected columns not found. Available: {reader.fieldnames}")
        for row in reader:
            t = (row.get(text_col) or "").strip()
            _id = (row.get(id_col) or "").strip()
            if t and _id:
                rows.append((_id, t))
    if not rows:
        return [], []
    ids, texts = zip(*rows)
    return list(ids), list(texts)

def main():
    ap = argparse.ArgumentParser(description="Embed CSV texts with LaBSE and save .npy (vectors) + .txt (ids).")
    ap.add_argument("--input", required=True, help="Input CSV (e.g., windows_with_headings.csv)")
    ap.add_argument("--text-col", required=True, help="Text column name (e.g., 'text' or 'sentence_text')")
    ap.add_argument("--id-col", required=True, help="ID column name (e.g., 'window_id' or 'sentence_id')")
    ap.add_argument("--out-npy", required=True, help="Output .npy path for vectors")
    ap.add_argument("--out-ids", required=True, help="Output .txt path for IDs (one per line)")
    ap.add_argument("--batch-size", type=int, default=64, help="Batch size (default: 64)")
    args = ap.parse_args()

    ids, texts = read_pairs(args.input, args.text_col, args.id_col)
    if not ids:
        print("[!] No rows with both id and text. Nothing to embed.")
        sys.exit(0)

    print(f"[i] Encoding {len(texts)} rows ...")
    vecs = embed_batch(
        texts,
        batch_size=args.batch_size,
        normalize=True
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.out_npy)), exist_ok=True)
    np.save(args.out_npy, vecs)
    with open(args.out_ids, 'w', encoding='utf-8') as f:
        for _id in ids:
            f.write(_id + '\n')

    print(f"[✓] Saved vectors → {args.out_npy}  (shape={vecs.shape})")
    print(f"[✓] Saved ids     → {args.out_ids}")

if __name__ == "__main__":
    main()
