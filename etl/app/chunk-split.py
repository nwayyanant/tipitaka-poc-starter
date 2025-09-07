import argparse
import csv
import os
import re
from typing import List, Dict, Any, Tuple

# ==============================
# Sentence split (user rule + refinements)
# ==============================
def split_into_sentences(text: str) -> List[str]:
    """
    Base rule:
    - Replace newlines with space
    - Track parentheses level; only end a sentence at '.' when paren_level == 0

    Extra refinements (requested):
    1) Do not start a new sentence with '(' : if a sentence begins with '(',
       merge it into the previous sentence.
    2) Standalone numbers (e.g., "2" or "2.") should not be a full sentence;
       instead, they should prefix the NEXT sentence: "2. <next sentence>".
    3) A trailing number at the end of a sentence (e.g., "... 12.") should be
       moved to the START of the NEXT sentence as a numbering prefix:
       "<current sentence sans number>" and then "12. <next sentence>".
    """
    text = text.replace('\n', ' ')
    sentences = []
    current = []
    paren_level = 0

    parts = re.split(r'(\.|\(|\))', text)

    i = 0
    while i < len(parts):
        part = parts[i]
        if part == '(':
            paren_level += 1
            if current:
                current[-1] += part
            else:
                current.append(part)
        elif part == ')':
            paren_level = max(paren_level - 1, 0)
            current.append(part)
        elif part == '.' and paren_level == 0:
            current.append(part)
            sentence = ''.join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []
        else:
            current.append(part)
        i += 1

    # tail (no trailing '.')
    tail = ''.join(current).strip()
    if tail:
        sentences.append(tail)

    # --- Post-processing passes ---
    # Pass A: merge sentences that start with '(' into the previous sentence
    merged = []
    for s in sentences:
        s_clean = s.strip()
        if s_clean.startswith('(') and merged:
            merged[-1] = (merged[-1].rstrip() + ' ' + s_clean).strip()
        else:
            merged.append(s_clean)
    sentences = merged

    # Pass B + C combined:
    # - If a sentence is only a number (e.g., "2" or "2."), attach it as a prefix to the next sentence.
    # - If a sentence ends with a number (e.g., "... 12."), move that number to the start of the next sentence.
    out = []
    i = 0
    while i < len(sentences):
        s = sentences[i].strip()

        # Standalone number?
        m_num_only = re.fullmatch(r'(\d+)(\.)?', s)
        if m_num_only and (i + 1) < len(sentences):
            num = m_num_only.group(1)
            # prefix next sentence
            sentences[i+1] = f"{num}. {sentences[i+1].lstrip()}"
            i += 1
            continue

        # Trailing number at end (space + digits + .)
        m_trail = re.match(r'^(.*?)(?:\s+)(\d+)\.$', s)
        if m_trail and (i + 1) < len(sentences):
            base = m_trail.group(1).strip()
            num = m_trail.group(2)
            if base:
                out.append(base)
            # prefix next
            sentences[i+1] = f"{num}. {sentences[i+1].lstrip()}"
            i += 1
            continue

        out.append(s)
        i += 1

    # Normalize whitespace
    out = [re.sub(r'\s+', ' ', s).strip() for s in out if s and s.strip()]
    return out

# ==============================
# Helpers
# ==============================
def whitespace_tokens(text: str) -> List[str]:
    return [t for t in re.split(r'\s+', text.strip()) if t != '']

def join_tokens(tokens: List[str]) -> str:
    return ' '.join(tokens).strip()

def ensure_dir(p: str):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)

def chunk_token_ranges(num_tokens: int, chunk_size: int) -> List[Tuple[int, int]]:
    """
    Return 1-based inclusive ranges: [(1, min(chunk_size, N)), (chunk_size+1, ...), ...]
    """
    ranges = []
    start = 1
    while start <= num_tokens:
        end = min(start + chunk_size - 1, num_tokens)
        ranges.append((start, end))
        start = end + 1
    return ranges

def subchunk_ranges(chunk_len: int, sub_size: int) -> List[Tuple[int, int]]:
    """
    1-based inclusive ranges within a chunk.
    """
    ranges = []
    start = 1
    while start <= chunk_len:
        end = min(start + sub_size - 1, chunk_len)
        ranges.append((start, end))
        start = end + 1
    return ranges

def make_chunk_id(prefix: str, idx: int, width: int) -> str:
    return f"{prefix}{idx:0{width}d}"

def make_sub_id(chunk_id: str, sub_idx: int, width: int) -> str:
    return f"{chunk_id}-SUB{sub_idx:0{width}d}"

def make_sentence_id(chunk_id: str, sub_idx: int, sent_idx: int, width: int) -> str:
    return f"{chunk_id}-SUB{sub_idx:0{width}d}-S{sent_idx:0{width}d}"

# ==============================
# Windows (sizes 2/3)
# ==============================
def build_windows_for_chunk(chunk_id: str, sents: List[Dict[str, Any]], size: int) -> List[Dict[str, Any]]:
    out = []
    if len(sents) < size:
        return out
    run = 1
    for i in range(0, len(sents) - size + 1):
        group = sents[i:i+size]
        text = ' '.join([g['sentence_text'].strip() for g in group]).strip()
        text = re.sub(r'\s+', ' ', text)

        row: Dict[str, Any] = {
            'window_id': f"{chunk_id}-W{size}-{run:04d}",
            'chunk_id': chunk_id,
            'size': size,
            'left_sentence_id': group[0]['sentence_id'],
            'right_sentence_id': group[-1]['sentence_id'],
            'order_idx': run,
            'text': text,
        }
        # token spans if available
        tstarts = [g['token_start'] for g in group if isinstance(g.get('token_start'), int)]
        tends = [g['token_end'] for g in group if isinstance(g.get('token_end'), int)]
        if tstarts and tends:
            row['token_start'] = min(tstarts)
            row['token_end'] = max(tends)
        out.append(row)
        run += 1
    return out

# ==============================
# Pipeline
# ==============================
def run_pipeline(input_txt: str,
                 out_chunks: str,
                 out_subchunks: str,
                 out_sentences: str,
                 out_windows: str,
                 prefix: str = "MAIN",
                 id_width: int = 3,
                 chunk_size: int = 8000,
                 sub_size: int = 200,
                 tokenizer: str = "whitespace"):
    # Load
    with open(input_txt, 'r', encoding='utf-8-sig') as f:
        raw = f.read()

    # Tokenize
    tokens = whitespace_tokens(raw) if tokenizer == "whitespace" else whitespace_tokens(raw)
    N = len(tokens)

    # Build chunk ranges (global token index, 1-based)
    cranges = chunk_token_ranges(N, chunk_size)

    # Outputs accumulators
    chunks_out: List[Dict[str, Any]] = []
    subs_out: List[Dict[str, Any]] = []
    sents_out: List[Dict[str, Any]] = []

    # Iterate chunks
    for cidx, (cstart, cend) in enumerate(cranges, start=1):
        chunk_id = make_chunk_id(prefix, cidx, id_width)
        chunk_tokens = tokens[cstart-1:cend]
        chunk_text = join_tokens(chunk_tokens)

        # record chunk
        chunks_out.append({
            'chunk_id': chunk_id,
            'token_start': cstart,
            'token_end': cend,
            'chunk_text': chunk_text
        })

        # Subchunks (within chunk, 1-based)
        sranges = subchunk_ranges(len(chunk_tokens), sub_size)
        for sidx, (sstart, send) in enumerate(sranges, start=1):
            sub_id = make_sub_id(chunk_id, sidx, id_width)
            # Map to global token indices
            gstart = cstart + (sstart - 1)
            gend = cstart + (send - 1)
            sub_tokens = chunk_tokens[sstart-1:send]
            sub_text = join_tokens(sub_tokens)

            subs_out.append({
                'subchunk_id': sub_id,
                'chunk_id': chunk_id,
                'order_idx': sidx,
                'token_start': gstart,
                'token_end': gend,
                'subchunk_text': sub_text
            })

        # Sentences: split chunk_text into sentences, then compute token spans
        local_ptr = 1  # 1..len(chunk_tokens)
        sent_idx = 0
        sranges_local = sranges  # local to chunk

        for s in split_into_sentences(chunk_text):
            s_trim = s.strip()
            if not s_trim:
                continue
            s_tok = whitespace_tokens(s_trim)
            tcount = len(s_tok)
            if tcount == 0:
                continue
            s_start_local = local_ptr
            s_end_local = local_ptr + tcount - 1
            s_start_local = max(1, s_start_local)
            s_end_local = min(len(chunk_tokens), s_end_local)

            # Determine subchunk index where sentence starts (optional)
            start_sub_idx = 0
            for idx_sc, (a,b) in enumerate(sranges_local, start=1):
                if a <= s_start_local <= b:
                    start_sub_idx = idx_sc
                    break

            sent_idx += 1
            sentence_id = make_sentence_id(chunk_id, start_sub_idx if start_sub_idx>0 else 1, sent_idx, id_width)

            # Map to global
            g_s = cstart + (s_start_local - 1)
            g_e = cstart + (s_end_local - 1)

            sents_out.append({
                'sentence_id': sentence_id,
                'chunk_id': chunk_id,
                'subchunk_id': make_sub_id(chunk_id, start_sub_idx if start_sub_idx>0 else 1, id_width),
                'order_idx': sent_idx,
                'token_start': g_s,
                'token_end': g_e,
                'sentence_text': s_trim
            })

            local_ptr = s_end_local + 1
            if local_ptr > len(chunk_tokens):
                break  # no more tokens left in this chunk

    # Write outputs
    ensure_dir(out_chunks)
    ensure_dir(out_subchunks)
    ensure_dir(out_sentences)

    with open(out_chunks, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['chunk_id','token_start','token_end','chunk_text'])
        w.writeheader()
        for r in chunks_out:
            w.writerow(r)

    with open(out_subchunks, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['subchunk_id','chunk_id','order_idx','token_start','token_end','subchunk_text'])
        w.writeheader()
        for r in subs_out:
            w.writerow(r)

    with open(out_sentences, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['sentence_id','chunk_id','subchunk_id','order_idx','token_start','token_end','sentence_text'])
        w.writeheader()
        for r in sents_out:
            w.writerow(r)

    # Build windows (2/3) per chunk from sents_out
    by_chunk: Dict[str, List[Dict[str, Any]]] = {}
    for r in sents_out:
        by_chunk.setdefault(r['chunk_id'], []).append(r)
    for cid in by_chunk:
        by_chunk[cid].sort(key=lambda r: r['order_idx'])

    windows_all: List[Dict[str, Any]] = []
    for cid, lst in by_chunk.items():
        windows_all += build_windows_for_chunk(cid, lst, 2)
        windows_all += build_windows_for_chunk(cid, lst, 3)

    ensure_dir(out_windows)
    base_fields = ['window_id','chunk_id','size','left_sentence_id','right_sentence_id','order_idx','text']
    opt_fields = []
    if any('token_start' in r for r in windows_all):
        opt_fields.append('token_start')
    if any('token_end' in r for r in windows_all):
        opt_fields.append('token_end')
    with open(out_windows, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=base_fields + opt_fields)
        w.writeheader()
        for r in windows_all:
            w.writerow({k: r.get(k, '') for k in base_fields + opt_fields})

    print(f"[✓] chunks:     {len(chunks_out)} → {out_chunks}")
    print(f"[✓] subchunks:  {len(subs_out)} → {out_subchunks}")
    print(f"[✓] sentences:  {len(sents_out)} → {out_sentences}")
    print(f"[✓] windows:    {len(windows_all)} → {out_windows}")
    print("[i] Boundary: windows within each chunk; sub-chunk crossings allowed; cross-chunk disabled.")

def main():
    ap = argparse.ArgumentParser(description="Pipeline: Steps 1–6 + windows (2/3) with enhanced sentence rules.")
    ap.add_argument('--input', required=True, help="Path to cleaned Pali .txt")
    ap.add_argument('--outdir', required=True, help="Output directory (e.g., outputs)")
    ap.add_argument('--prefix', default='MAIN', help="Chunk ID prefix (default: MAIN)")
    ap.add_argument('--id-width', type=int, default=3, help="Zero pad width for numbers (default: 3 → 001)")
    ap.add_argument('--chunk-size', type=int, default=8000, help="Tokens per chunk (default: 8000)")
    ap.add_argument('--sub-size', type=int, default=200, help="Tokens per subchunk (default: 200)")
    ap.add_argument('--tokenizer', default='whitespace', choices=['whitespace'], help="Tokenizer (default: whitespace)")
    args = ap.parse_args()

    out_chunks = os.path.join(args.outdir, 'chunks.csv')
    out_subchunks = os.path.join(args.outdir, 'subchunks_200.csv')
    out_sentences = os.path.join(args.outdir, 'sentences_from_200.csv')
    out_windows = os.path.join(args.outdir, 'windows_2_3.csv')

    run_pipeline(args.input, out_chunks, out_subchunks, out_sentences, out_windows,
                 prefix=args.prefix, id_width=args.id_width,
                 chunk_size=args.chunk_size, sub_size=args.sub_size,
                 tokenizer=args.tokenizer)

if __name__ == '__main__':
    main()
