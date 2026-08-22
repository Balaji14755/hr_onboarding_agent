from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from config import Config
from rag.vectorstore import get_vectorstore, initialize_vectorstore

def get_retriever(k: int = Config.RETRIEVER_K):
    """Return standard LangChain retriever interface."""
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})

def retrieve_context(query: str, k: int = Config.RETRIEVER_K) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Retrieve relevant document chunks for a query and return:
    1. Formatted context string for LLM prompt
    2. List of source citation dicts for UI display
    """
    vectorstore = get_vectorstore()
    
    # Check if empty, initialize if needed
    if vectorstore._collection.count() == 0:
        vectorstore = initialize_vectorstore()

    # Perform similarity search
    docs = vectorstore.similarity_search(query, k=k)

    context_blocks = []
    sources: List[Dict[str, Any]] = []
    seen_citations = set()

    for idx, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        doc_title = meta.get("document_title", "HR Document")
        page = meta.get("page", 1)
        source_file = meta.get("source", "document.pdf")
        citation = meta.get("citation", f"{doc_title} — Page {page}")

        context_blocks.append(
            f"--- DOCUMENT CHUNK {idx} [{citation}] ---\n{doc.page_content.strip()}\n"
        )

        # Deduplicate sources for clean UI rendering
        source_key = (doc_title, page)
        if source_key not in seen_citations:
            seen_citations.add(source_key)
            sources.append({
                "document_title": doc_title,
                "source": source_file,
                "page": page,
                "citation": citation,
                "snippet": doc.page_content.strip()[:240] + ("..." if len(doc.page_content) > 240 else "")
            })

    context_str = "\n".join(context_blocks)
    return context_str, sources
