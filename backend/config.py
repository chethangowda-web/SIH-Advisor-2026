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

# Validate
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env file!")
