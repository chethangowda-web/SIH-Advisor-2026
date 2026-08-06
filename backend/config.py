import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "featherless")

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

FEATHERLESS_API_KEY: str = os.getenv("FEATHERLESS_API_KEY", "")
FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"

FEATHERLESS_MODEL: str = os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen3-32B")

OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-32b")
CHAT_MODEL: str = os.getenv("CHAT_MODEL", "meta-llama/llama-3.3-70b-instruct")

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME: str = "sih_projects"

DATA_PATH: str = os.getenv("DATA_PATH", "./data/sih_winners.json")

PORT: int = int(os.getenv("PORT", 8000))

_active_key = (
    FEATHERLESS_API_KEY if LLM_PROVIDER == "featherless" else OPENROUTER_API_KEY
)

if not _active_key:
    print(f"[warn] {LLM_PROVIDER.upper()} API key is not set. LLM-powered endpoints will report a clear "
          "error until you add it to your .env file. UI, health and data endpoints still work.")