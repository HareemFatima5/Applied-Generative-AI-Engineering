import os
import re
import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Configuration constants
DOCUMENTS_DIR = "documents"
VECTOR_STORE_DIR = "vector_store"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  
CHUNK_SIZE = 800         
CHUNK_OVERLAP = 150
EMBEDDING_BATCH_SIZE = 64
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def load_documents(documents_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """Load all supported documents from the specified directory."""
    docs = []
    for path in sorted(Path(documents_dir).glob("*")):
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        if suffix in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            pages = [(None, text)] if text.strip() else []
        elif suffix == ".pdf":
            pages = _extract_pdf_pages(path)
        else:
            continue

        if pages:
            docs.append({"source": path.name, "pages": pages})

    if not docs:
        raise ValueError(f"No supported documents found in '{documents_dir}'.")
    return docs


def _extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """Extract text from PDF using PyMuPDF or pdfplumber as fallback."""
    # Try PyMuPDF first (faster, more reliable)
    try:
        import fitz
        doc = fitz.open(str(path))
        pages = [(i + 1, page.get_text()) for i, page in enumerate(doc)]
        doc.close()
        if any(t.strip() for _, t in pages):
            return [(n, t) for n, t in pages if t.strip()]
    except Exception as e:
        print(f"  [warn] PyMuPDF failed on '{path.name}': {e}")

    # Fallback to pdfplumber
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    pages.append((i + 1, page_text))
        if pages:
            return pages
    except Exception as e:
        print(f"  [warn] pdfplumber failed on '{path.name}': {e}")

    print(f"  [warn] No text could be extracted from '{path.name}' (likely a scanned/image-only PDF).")
    return []


def clean_text(text: str) -> str:
    """Clean text by normalizing whitespace while preserving paragraph breaks."""
    text = re.sub(r"[ \t]+", " ", text)  # Collapse spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)  # Limit consecutive newlines
    return text.strip()


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs based on blank lines."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [re.sub(r"\s+", " ", p).strip() for p in paragraphs if p.strip()]


def chunk_page_text(text: str) -> list[str]:
    """Split page text into overlapping chunks while respecting paragraph boundaries."""
    text = clean_text(text)
    if not text:
        return []

    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks = []
    current = ""

    for para in paragraphs:
        # Handle oversized paragraphs by hard-slicing
        if len(para) > CHUNK_SIZE:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_hard_slice(para))
            continue

        # Add paragraph to current chunk if within size limit
        candidate = f"{current} {para}".strip() if current else para
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    return _add_overlap(chunks)


def _hard_slice(text: str) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + CHUNK_SIZE, length)
        chunks.append(text[start:end])
        if end == length:
            break
        start = end - CHUNK_OVERLAP
    return chunks


def _add_overlap(chunks: list[str]) -> list[str]:
    """Add overlapping text between consecutive chunks for context preservation."""
    if len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-CHUNK_OVERLAP:]
        overlapped.append(f"{prev_tail} {chunks[i]}".strip())
    return overlapped


def build_chunks(docs: list[dict]) -> list[dict]:
    """Build text chunks from documents with metadata."""
    all_chunks = []
    for doc in docs:
        chunk_idx = 0
        for page_num, page_text in doc["pages"]:
            pieces = chunk_page_text(page_text)
            for piece in pieces:
                all_chunks.append({
                    "id": f"{doc['source']}::chunk_{chunk_idx}",
                    "source": doc["source"],
                    "chunk_index": chunk_idx,
                    "page": page_num,
                    "text": piece,
                })
                chunk_idx += 1
    return all_chunks


def build_vector_store(chunks: list[dict], model_name: str = EMBEDDING_MODEL_NAME, 
                       output_dir: str = VECTOR_STORE_DIR, batch_size: int = EMBEDDING_BATCH_SIZE,
                       progress_callback=None) -> None:
    """Generate embeddings and build FAISS vector store."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = [c["text"] for c in chunks]
    total = len(texts)
    print(f"Generating embeddings for {total} chunks")

    # Process embeddings in batches
    batch_embeddings = []
    for start in range(0, total, batch_size):
        batch_texts = texts[start:start + batch_size]
        batch_vectors = model.encode(batch_texts, convert_to_numpy=True, normalize_embeddings=True)
        batch_embeddings.append(batch_vectors)

        done = min(start + batch_size, total)
        if progress_callback:
            progress_callback(done, total)
        else:
            print(f"  embedded {done}/{total} chunks")

    embeddings = np.vstack(batch_embeddings).astype("float32")

    # Build FAISS index with cosine similarity (inner product on normalized vectors)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save index and metadata
    faiss.write_index(index, os.path.join(output_dir, "index.faiss"))
    with open(os.path.join(output_dir, "metadata.pkl"), "wb") as f:
        pickle.dump({"chunks": chunks, "model_name": model_name, "dimension": dimension}, f)

    print(f"Vector store saved to '{output_dir}' with {len(chunks)} chunks")


def main() -> None:
    print("Loading documents")
    docs = load_documents()
    print(f"Loaded {len(docs)} document(s)")

    print("Splitting documents into chunks")
    chunks = build_chunks(docs)
    print(f"Created {len(chunks)} chunk(s)")

    build_vector_store(chunks)
    print("Done!")


if __name__ == "__main__":
    main()
