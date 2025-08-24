from etl.data_loader import prepare_chunks
from etl.weaviate_client import get_client, ensure_schema
from etl.config import BATCH_SIZE, DROP_AND_RECREATE

def run_pipeline():
    client = get_client()
    if DROP_AND_RECREATE:
        ensure_schema(client)

    df = prepare_chunks("data/chunk.csv")

    with client.batch as batch:
        batch.batch_size = BATCH_SIZE
        for _, row in df.iterrows():
            batch.add_data_object(
                {"pali_text": row["pali_text"], "translation": row.get("translation", "")},
                "Chunk"
            )
