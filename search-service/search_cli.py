#!/usr/bin/env python3
import argparse
from search_client import SearchClient

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="Window")
    ap.add_argument("--mode", choices=["vector","hybrid"], default="vector")
    ap.add_argument("--query", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--alpha", type=float, default=0.5)
    args = ap.parse_args()

    sc = SearchClient()
    qvec = sc.encode_query(args.query)

    if args.mode=="hybrid":
        res = sc.search_vector(args.collection, qvec, top_k=args.k, hybrid_query=args.query, alpha=args.alpha)
    else:
        res = sc.search_vector(args.collection, qvec, top_k=args.k)

    print(f"[results] {len(res.objects)} objects")
    for i,o in enumerate(res.objects or [], start=1):
        print(f"{i:>2}. {o.properties.get('text','')[:100]}...")

if __name__=="__main__":
    main()
