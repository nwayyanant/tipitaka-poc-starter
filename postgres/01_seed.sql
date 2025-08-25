-- Import chunks
\copy chunk(chunk_id, order_idx, pali_text)
FROM '/docker-entrypoint-initdb.d/data/chunk.csv'
DELIMITER ',' CSV HEADER;

-- Import subchunks
\copy subchunk(subchunk_id, chunk_id, order_idx, token_start, token_end, pali_text)
FROM '/docker-entrypoint-initdb.d/data/subchunk.csv'
DELIMITER ',' CSV HEADER;

-- Import sentences
\copy sentence(sentence_id, chunk_id, subchunk_id, order_idx, pali_text)
FROM '/docker-entrypoint-initdb.d/data/sentence.csv'
DELIMITER ',' CSV HEADER;

-- Import windows
\copy sentence_window(window_id, chunk_id, size, left_sentence_id, right_sentence_id, order_idx, text)
FROM '/docker-entrypoint-initdb.d/data/windows.csv'
DELIMITER ',' CSV HEADER;
