import os
from dotenv import load_dotenv

load_dotenv()

# Groq LLM Config
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Embedding Config
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ChromaDB Config
CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME: str = "sih_projects"

# Data Config
DATA_PATH: str = os.getenv("DATA_PATH", "./data/sih_winners.json")

# Server Config
PORT: int = int(os.getenv("PORT", 8000))

# Do NOT crash at import time when the key is missing. The server must still boot
# so the UI and static endpoints work; LLM calls surface a clear error at runtime
# (and main.py returns a friendly JSON message instead of a bare 500).
if not GROQ_API_KEY:
    print("[warn] GROQ_API_KEY is not set. LLM-powered endpoints will report a clear "
          "error until you add it to your .env file. UI, health and data endpoints still work.")