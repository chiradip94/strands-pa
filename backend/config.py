from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "llm_base_url": os.getenv("LLM_BASE_URL"),
    "llm_api_key": os.getenv("LLM_API_KEY"),
    "llm_model": os.getenv("LLM_MODEL"),
    "user_collection": os.getenv("USER_COLLECTION_NAME", "user-data"),
    "qdrant_url": os.getenv("QDRANT_URL"),
    "qdrant_api_key": os.getenv("QDRANT_API_KEY"),
    "qdrant_model": os.getenv("QDRANT_MODEL"),
    "qdrant_vector_size": int(os.getenv("QDRANT_VECTOR_SIZE", "1536")),
    "mongo_uri": os.getenv("MONGO_URI"),
    "mongo_db": os.getenv("MONGO_DB"),
}