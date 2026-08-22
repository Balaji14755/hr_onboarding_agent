import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymupdf
from config import Config

# Human readable document titles mapping
DOC_TITLES = {
    "benefits_faq.pdf": "Benefits FAQ",
    "it_setup.pdf": "IT Setup Guide",
    "employee_handbook.pdf": "Employee Handbook",
    "security_policy.pdf": "Security Policy"
}

def clean_text(text: str) -> str:
    """Clean extracted PDF text from artifact noise."""
    # Replace non-breaking spaces and fix weird unicode bullet points if any
    text = text.replace('\xa0', ' ').replace('\u2022', '-').replace('\ufffd', '')
    # Remove excessive blank lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def load_single_pdf(pdf_path: Path) -> List[Document]:
    """
    Load a single PDF page-by-page using PyMuPDF and extract Document objects
    with rich metadata (document title, filename, page number).
    """
    doc_name = pdf_path.name
    doc_title = DOC_TITLES.get(doc_name, doc_name.replace("_", " ").replace(".pdf", "").title())
    documents = []

    try:
        pdf = pymupdf.open(str(pdf_path))
        total_pages = len(pdf)
        
        for page_num in range(total_pages):
            page = pdf[page_num]
            text = page.get_text("text")
            cleaned = clean_text(text)
            
            if cleaned:
                metadata = {
                    "source": doc_name,
                    "document_title": doc_title,
                    "page": page_num + 1,
                    "total_pages": total_pages,
                    "citation": f"{doc_title} — Page {page_num + 1}"
                }
                documents.append(Document(page_content=cleaned, metadata=metadata))
        
        pdf.close()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        # Fallback to PyPDF if PyMuPDF fails
        try:
            import pypdf
            reader = pypdf.PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                cleaned = clean_text(text)
                if cleaned:
                    metadata = {
                        "source": doc_name,
                        "document_title": doc_title,
                        "page": idx + 1,
                        "total_pages": total_pages,
                        "citation": f"{doc_title} — Page {idx + 1}"
                    }
                    documents.append(Document(page_content=cleaned, metadata=metadata))
        except Exception as e2:
            print(f"Fallback PyPDF also failed for {pdf_path}: {e2}")

    return documents

def load_and_chunk_documents(data_dir: Path = Config.DATA_DIR) -> List[Document]:
    """
    Load all PDF files from the data directory and chunk them with metadata preservation.
    """
    all_pages: List[Document] = []
    pdf_files = list(data_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {data_dir}. Generating mock documents...")
        from generate_mock_docs import generate_all_mock_documents
        generate_all_mock_documents()
        pdf_files = list(data_dir.glob("*.pdf"))

    for pdf_path in sorted(pdf_files):
        pages = load_single_pdf(pdf_path)
        all_pages.extend(pages)

    # Chunk documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "•", "- ", ". ", " ", ""]
    )

    chunked_docs = text_splitter.split_documents(all_pages)
    return chunked_docs
