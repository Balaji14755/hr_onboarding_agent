"""RAG Package for HR Onboarding Assistant."""
from rag.loader import load_and_chunk_documents
from rag.vectorstore import get_vectorstore, initialize_vectorstore
from rag.retriever import get_retriever, retrieve_context

__all__ = [
    "load_and_chunk_documents",
    "get_vectorstore",
    "initialize_vectorstore",
    "get_retriever",
    "retrieve_context",
]
