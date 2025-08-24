"""Weaviate schema management.


Creates (and optionally drops) the class used to store Tipitaka chunks.
Run this script manually to set up schema before loading data.
"""
import weaviate
import logging
from . import config


logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL.upper())


def create_schema():
client = weaviate.Client(url=config.WEAVIATE_URL)
class_obj = {
"class": config.CLASS_NAME,
"description": "Tipitaka text chunks and their embeddings",
"vectorizer": "text2vec-transformers",
"moduleConfig": {
"text2vec-transformers": {
"vectorizeClassName": False,
}
},
"properties": [
{"name": "chunk_id", "dataType": ["string"]},
{"name": config.TEXT_COLUMN, "dataType": ["text"]},
{"name": "window_id", "dataType": ["string"]},
{"name": config.WINDOW_COLUMN, "dataType": ["text"]},
],
}


if config.DROP_AND_RECREATE:
if client.schema.exists(config.CLASS_NAME):
logger.info(f"Dropping existing class {config.CLASS_NAME}")
client.schema.delete_class(config.CLASS_NAME)


if not client.schema.exists(config.CLASS_NAME):
logger.info(f"Creating class {config.CLASS_NAME}")
client.schema.create_class(class_obj)
else:
logger.info(f"Class {config.CLASS_NAME} already exists, skipping create.")


def main():
config.summary()
create_schema()
logger.info("Schema setup complete.")


if __name__ == "__main__":
main()
