import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-32b")
CHAT_MODEL: str = os.getenv("CHAT_MODEL", "meta-llama/llama-3.3-70b-instruct")

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME: str = "sih_projects"

DATA_PATH: str = os.getenv("DATA_PATH", "./data/sih_winners.json")

PORT: int = int(os.getenv("PORT", 8000))

if not OPENROUTER_API_KEY:
    print("[warn] OPENROUTER_API_KEY is not set. LLM-powered endpoints will report a clear "
          "error until you add it to your .env file. UI, health and data endpoints still work.")