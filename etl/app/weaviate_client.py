import weaviate
from etl.config import WEAVIATE_URL

def get_client():
    return weaviate.Client(WEAVIATE_URL)

def ensure_schema(client):
    schema = {
        "classes": [
            {
                "class": "Chunk",
                "properties": [
                    {"name": "pali_text", "dataType": ["text"]},
                    {"name": "translation", "dataType": ["text"]},
                ],
            }
        ]
    }
    client.schema.delete_all()
    client.schema.create(schema)
