import os
import psycopg2
import pandas as pd
from etl.config import POSTGRES_CONFIG

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

TABLES = {
    "chunk": "chunk.csv",
    "subchunk": "subchunk.csv",
    "sentence": "sentence.csv",
    "sentence_window": "windows.csv",
}

def load_csv_to_postgres(table, file_path, conn):
    print(f"Loading {file_path} into {table}...")
    df = pd.read_csv(file_path)
    # Save temp file as tab-delimited for copy_from
    tmp_path = file_path + ".tmp"
    df.to_csv(tmp_path, sep="\t", index=False, header=False)

    with conn.cursor() as cur, open(tmp_path, "r", encoding="utf-8") as f:
        cur.copy_from(f, table, sep="\t", null="")
    conn.commit()
    print(f"✔ Imported {len(df)} rows into {table}.")

def main():
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    try:
        for table, csv_file in TABLES.items():
            file_path = os.path.join(DATA_DIR, csv_file)
            if os.path.exists(file_path):
                load_csv_to_postgres(table, file_path, conn)
            else:
                print(f"⚠️  CSV not found: {file_path}, skipping.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
