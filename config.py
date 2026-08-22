import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

def _get_secret(key: str, default: str = "") -> str:
    """Get a config value from environment, then Streamlit secrets as fallback."""
    val = os.getenv(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default

class Config:
    # Groq API Configuration
    GROQ_API_KEY: str = _get_secret("GROQ_API_KEY")
    GROQ_MODEL: str = _get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Supported Groq Models for fallback/selection
    AVAILABLE_MODELS: list[str] = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    # Embeddings Configuration
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip()

    # Paths
    DATA_DIR: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    DATABASE_DIR: Path = BASE_DIR / "database"
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "database/onboarding.db")
    CHROMA_DIR: Path = BASE_DIR / os.getenv("CHROMA_DIR", "database/chroma_db")

    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    RETRIEVER_K: int = 4

    @classmethod
    def ensure_directories(cls):
        """Ensure that all required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Ensure directories are created on import
Config.ensure_directories()
