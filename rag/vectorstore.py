import shutil
from pathlib import Path
from typing import Optional
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import Config
from rag.loader import load_and_chunk_documents

_cached_embeddings = None
_cached_vectorstore = None

def get_embeddings():
    """Get or instantiate cached HuggingFaceEmbeddings."""
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    return _cached_embeddings

def get_vectorstore() -> Chroma:
    """Get the Chroma vectorstore instance."""
    global _cached_vectorstore
    embeddings = get_embeddings()
    
    if _cached_vectorstore is None:
        _cached_vectorstore = Chroma(
            collection_name="hr_onboarding_docs",
            embedding_function=embeddings,
            persist_directory=str(Config.CHROMA_DIR)
        )
    return _cached_vectorstore

def initialize_vectorstore(force_reload: bool = False) -> Chroma:
    """
    Initialize vector store with documents from data directory.
    If already populated and not force_reload, reuses existing store.
    """
    global _cached_vectorstore
    Config.ensure_directories()
    
    embeddings = get_embeddings()
    
    if force_reload and Config.CHROMA_DIR.exists():
        print("Force reloading vector store: clearing existing ChromaDB...")
        _cached_vectorstore = None
        try:
            shutil.rmtree(Config.CHROMA_DIR)
        except Exception as e:
            print(f"Warning clearing chroma dir: {e}")
        Config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    vectorstore = Chroma(
        collection_name="hr_onboarding_docs",
        embedding_function=embeddings,
        persist_directory=str(Config.CHROMA_DIR)
    )

    # Check if documents exist in collection
    existing_count = vectorstore._collection.count()
    if existing_count == 0 or force_reload:
        print(f"Indexing HR documents into ChromaDB ({Config.DATA_DIR})...")
        chunks = load_and_chunk_documents(Config.DATA_DIR)
        if chunks:
            vectorstore.add_documents(chunks)
            print(f"[OK] Ingested {len(chunks)} chunks into ChromaDB.")
        else:
            print("[Warning] No document chunks found to ingest.")
    else:
        print(f"[OK] ChromaDB already contains {existing_count} chunks.")

    _cached_vectorstore = vectorstore
    return vectorstore
