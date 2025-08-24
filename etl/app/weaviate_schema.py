import weaviate




def ensure_class(client: weaviate.Client, class_name: str = "TipitakaChunk") -> None:
schema = client.schema.get()
class_names = {c["class"] for c in schema.get("classes", [])}
if class_name in class_names:
return


class_obj = {
"class": class_name,
"description": "Pali Tipitaka chunks and optional sliding windows",
"vectorizer": "text2vec-transformers",
"moduleConfig": {
"text2vec-transformers": {
"poolingStrategy": "mean",
"vectorizeClassName": False,
}
},
"properties": [
{"name": "chunk_id", "dataType": ["text"], "description": "Source chunk id"},
{"name": "text", "dataType": ["text"], "description": "Primary Pali text"},
{"name": "window_text", "dataType": ["text"], "description": "Optional window text"},
],
}


client.schema.create_class(class_obj)