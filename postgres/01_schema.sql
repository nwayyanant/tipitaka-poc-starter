-- ================================
-- 1. Chunks (8000 tokens each)
-- ================================
DROP TABLE IF EXISTS chunk CASCADE;

CREATE TABLE chunk (
    chunk_id TEXT PRIMARY KEY,              -- e.g. chunk_000001
    order_idx INT NOT NULL,                 -- 1,2,3 in sequence
    pali_text TEXT NOT NULL                 -- big 8000-token slice
);

-- Index for lookups in order
CREATE INDEX idx_chunk_order
    ON chunk(order_idx);


-- ================================
-- 2. Subchunks (200 tokens each)
-- ================================
DROP TABLE IF EXISTS subchunk CASCADE;

CREATE TABLE subchunk (
    subchunk_id TEXT PRIMARY KEY,           -- e.g. sc_000001_001
    chunk_id TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    order_idx INT NOT NULL,                 -- position inside chunk
    token_start INT,
    token_end INT,
    pali_text TEXT NOT NULL
);

-- Index: find subchunks by chunk and order
CREATE INDEX idx_subchunk_chunk_order
    ON subchunk(chunk_id, order_idx);


-- ================================
-- 3. Sentences (1 sentence each)
-- ================================
DROP TABLE IF EXISTS sentence CASCADE;

CREATE TABLE sentence (
    sentence_id TEXT PRIMARY KEY,           -- e.g. s_000001_001_001
    chunk_id TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    subchunk_id TEXT NOT NULL REFERENCES subchunk(subchunk_id) ON DELETE CASCADE,
    order_idx INT NOT NULL,                 -- position inside subchunk
    pali_text TEXT NOT NULL
);

-- Indexes: common lookups
CREATE INDEX idx_sentence_chunk_order
    ON sentence(chunk_id, order_idx);

CREATE INDEX idx_sentence_subchunk_order
    ON sentence(subchunk_id, order_idx);


-- ================================
-- 4. Windows (2-sentence / 3-sentence)
-- ================================
DROP TABLE IF EXISTS sentence_window CASCADE;

CREATE TABLE sentence_window (
    window_id TEXT PRIMARY KEY,             -- e.g. w_chunk0001_2_0001
    chunk_id TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    size INT NOT NULL,                      -- 2 or 3
    left_sentence_id TEXT NOT NULL REFERENCES sentence(sentence_id),
    right_sentence_id TEXT NOT NULL REFERENCES sentence(sentence_id),
    order_idx INT NOT NULL,                 -- position in chunk
    text TEXT NOT NULL
);

-- Indexes: lookup by chunk, by size, or by sentence boundaries
CREATE INDEX idx_window_chunk_size_order
    ON sentence_window(chunk_id, size, order_idx);

CREATE INDEX idx_window_left_sentence
    ON sentence_window(left_sentence_id);

CREATE INDEX idx_window_right_sentence
    ON sentence_window(right_sentence_id);
