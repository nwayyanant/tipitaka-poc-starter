#!/usr/bin/env python3
# etl/app/pipeline.py — simple one-shot: wait → schema → CSV insert → vectors → search
import os, sys, time, json, argparse, subprocess
from pathlib import Path
import urllib.request

# --- Config from env ---
WEAVIATE_URL  = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_GRPC = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
DATA_DIR      = Path(os.getenv("DATA_DIR", "/workspace/data"))
OUTPUTS_DIR   = Path(os.getenv("OUTPUTS_DIR", str(DATA_DIR / "outputs")))
WAIT_MAX_SEC  = int(os.getenv("WAIT_MAX_SEC", "600"))  # 10min default

APP_DIR = Path(__file__).resolve().parent

# Vector files (skip if missing)
VECTOR_FILES = [
    ("Window",   "windows_with_headings.csv",   "window_id",   "text",           "windows_ids.txt",   "windows_labse.npy"),
    ("Sentence", "sentences_with_headings.csv", "sentence_id", "sentence_text",   "sentences_ids.txt", "sentences_labse.npy"),
    ("Subchunk", "subchunks_200.csv",           "subchunk_id", "subchunk_text",   "subchunks_ids.txt", "subchunks_labse.npy"),
    ("Chunk",    "chunks.csv",                  "chunk_id",    "chunk_text",      "chunks_ids.txt",    "chunks_labse.npy"),
]

def sh(cmd, check=True):
    print("  $", " ".join(map(str, cmd)), flush=True)
    return subprocess.run(cmd, check=check)

def wait_ready(url: str, max_wait: int = WAIT_MAX_SEC):
    ready = url.rstrip("/") + "/v1/.well-known/ready"
    live  = url.rstrip("/") + "/v1/.well-known/live"
    start = time.time()
    print(f"⏳ Waiting for Weaviate: {ready}")
    while True:
        for probe in (ready, live):
            try:
                with urllib.request.urlopen(probe, timeout=3) as r:
                    body = (r.read().decode("utf-8", "ignore") or "").strip()
                    if r.status == 200:
                        # accept JSON {"status":"ready"} or plain 'OK' / contains 'ready' or empty 200
                        try:
                            if json.loads(body).get("status") == "ready":
                                print(f"✅ Weaviate ready (JSON) via {probe}")
                                return
                        except Exception:
                            if not body or body.upper() == "OK" or "ready" in body.lower():
                                print(f"✅ Weaviate ready (text='{body}') via {probe}")
                                return
            except Exception:
                pass
        if time.time() - start > max_wait:
            print("❌ Timed out waiting for Weaviate.", file=sys.stderr)
            sys.exit(1)
        time.sleep(2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=WEAVIATE_URL)
    ap.add_argument("--grpc-port", type=int, default=WEAVIATE_GRPC)
    args = ap.parse_args()

    print("=== Simple ETL Pipeline ===")
    print(f"WEAVIATE_URL={args.url}  GRPC={args.grpc_port}")
    print(f"OUTPUTS_DIR={OUTPUTS_DIR}\n")

    # 0) outputs must exist (manual provided)
    if not OUTPUTS_DIR.exists() or not any(OUTPUTS_DIR.iterdir()):
        print(f"❌ outputs not found at {OUTPUTS_DIR}. Please put your CSV/NPY files there.", file=sys.stderr)
        sys.exit(1)

    # 1) wait until Weaviate is up
    wait_ready(args.url)

    # scripts
    setup_script = APP_DIR / "weaviate_multitier_setup_and_search_patched.py"
    inserter     = APP_DIR / "insert_vectors_generic.py"
    searcher     = APP_DIR / "search_weaviate_labse_hybridfix.py"

    for p in (setup_script, inserter, searcher):
        if not p.exists():
            print(f"❌ Missing script: {p}", file=sys.stderr); sys.exit(1)

    # 2) schema
    print("🧱 Step 1/4: Schema setup")
    sh(["python", str(setup_script), "--url", args.url, "--grpc-port", str(args.grpc_port), "--setup"])

    # 3) CSV/BM25 insert
    print("📚 Step 2/4: Insert CSV (BM25)")
    sh([
        "python", str(setup_script),
        "--url", args.url, "--grpc-port", str(args.grpc_port),
        "--outdir", str(OUTPUTS_DIR),
        "--insert"
    ])

    # 4) vectors (present-only)
    print("🧠 Step 3/4: Insert LaBSE vectors (present-only)")
    for coll, csv, idcol, txtcol, ids, npy in VECTOR_FILES:
        csvp, idsp, npyp = OUTPUTS_DIR/csv, OUTPUTS_DIR/ids, OUTPUTS_DIR/npy
        if csvp.exists() and idsp.exists() and npyp.exists():
            print(f"   - {coll}: inserting vectors")
            sh([
                "python", str(inserter),
                "--url", args.url, "--grpc-port", str(args.grpc_port),
                "--collection", coll,
                "--csv", str(csvp),
                "--id-col", idcol, "--text-col", txtcol,
                "--ids", str(idsp), "--npy", str(npyp)
            ])
        else:
            print(f"   - {coll}: skip (missing {csv} or {ids} or {npy})")

    # 5) quick sanity search (non-blocking)
    print("🔎 Step 4/4: Sanity search")
    sh([
        "python", str(searcher),
        "--url", args.url, "--grpc-port", str(args.grpc_port),
        "--collection","Window","--mode","hybrid","--query","mettā","--k","5","--alpha","0.5"
    ], check=False)

    print("✅ Done.")

if __name__ == "__main__":
    main()
