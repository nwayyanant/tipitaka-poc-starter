# create_schema.py
from weaviate import Client
import os, time

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
client = Client(WEAVIATE_URL)

# Example: Window class using vectorizer none
window_class = {
  "class": "Window",
  "vectorizer": "none",
  "properties": [
    {"name": "window_id", "dataType": ["string"]},
    {"name": "text", "dataType": ["text"]},
    {"name": "chunk_id", "dataType": ["string"]},
    {"name": "path", "dataType": ["string"]},
    {"name": "h1", "dataType": ["string"]},
    {"name": "h2", "dataType": ["string"]},
    {"name": "h3", "dataType": ["string"]},
    {"name": "h4", "dataType": ["string"]},
    {"name": "h5", "dataType": ["string"]},
    {"name": "h6", "dataType": ["string"]}
  ]
}

if client.schema.contains("Window"):
    print("Window exists, skipping")
else:
    client.schema.create_class(window_class)
    print("Window class created")
