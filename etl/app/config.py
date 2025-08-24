from dotenv import load_dotenv
import os

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
DROP_AND_RECREATE = os.getenv("DROP_AND_RECREATE", "false").lower() == "true"
