import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OKF_DIR = DATA_DIR / "okf_bundle"
RAW_DOCS_DIR = DATA_DIR / "raw_docs"
STORAGE_DIR = ROOT_DIR / "storage"

# Try loading .env from project root, then fallback to parent directories
env_paths = [
    ROOT_DIR / ".env",
    ROOT_DIR.parent / ".env",
    ROOT_DIR.parent.parent / ".env",
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break

# API Keys & Models
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Qdrant Database Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_knowledge_chunks")

# Server Configuration
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")

# Embedding Configuration
VECTOR_DIMENSION = 3072  # gemini-embedding-001 dimension (or 768 / 1536 fallback)
CHUNK_SIZE = 360         # Characters per chunk for RAG fixed-size chunking
CHUNK_OVERLAP = 60       # Character overlap
