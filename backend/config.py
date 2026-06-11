from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "llm_base_url": os.getenv("LLM_BASE_URL"),
    "llm_api_key": os.getenv("LLM_API_KEY"),
    "llm_model": os.getenv("LLM_MODEL"),
}