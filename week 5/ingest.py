import os
import re
import pickle
import sqlite3
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = "documents"
VECTOR_STORE_DIR = "vector_store"
METADATA_DB_NAME = "metadata.db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  
CHUNK_SIZE = 800         
CHUNK_OVERLAP = 150
EMBEDDING_BATCH_SIZE = 64
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def load_documents(documents_dir: str = DOCUMENTS_DIR) -> list[dict]:
    docs = []
    for path in sorted(Path(documents_dir).glob("*")):
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        print(f"  reading '{path.name}'...")

        if suffix in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            pages = [(None, text, [])] if text.strip() else []
            metadata = {"title": None, "author": None, "subject": None,
                        "creation_date": None, "creation_date_iso": None,
                        "page_count": None, "title_guessed": False}
        elif suffix == ".pdf":
            pages = _extract_pdf_pages(path)
            metadata = _extract_pdf_metadata(path)
        else:
            continue

        if pages:
            docs.append({"source": path.name, "pages": pages, "metadata": metadata})

    if not docs:
        raise ValueError(f"No supported documents found in '{documents_dir}'.")
    return docs


def _parse_pdf_date(raw: str) -> str | None:
    if not raw:
        return None
    match = re.match(r"D:(\d{4})(\d{2})(\d{2})", raw)
    if not match:
        return None
    year, month, day = match.groups()
    try:
        return datetime(int(year), int(month), int(day)).date().isoformat()
    except ValueError:
        return None


def _extract_pdf_metadata(path: Path) -> dict:

    metadata = {"title": None, "author": None, "subject": None,
                "creation_date": None, "creation_date_iso": None,
                "page_count": None, "title_guessed": False}
    try:
        import fitz
        doc = fitz.open(str(path))
        pdf_info = doc.metadata or {}
        metadata["title"] = pdf_info.get("title") or None
        metadata["author"] = pdf_info.get("author") or None
        metadata["subject"] = pdf_info.get("subject") or None
        metadata["creation_date"] = pdf_info.get("creationDate") or None
        metadata["creation_date_iso"] = _parse_pdf_date(metadata["creation_date"])
        metadata["page_count"] = doc.page_count

        # fall back to guessing a title from the first page's largest text
        # when the pdf itself has no title in its metadata
        if not metadata["title"] and doc.page_count > 0:
            guessed = _guess_title_from_page(doc[0])
            if guessed:
                metadata["title"] = guessed
                metadata["title_guessed"] = True

        doc.close()
    except Exception as e:
        print(f"  [warn] could not read metadata from '{path.name}': {e}")
    return metadata


def _guess_title_from_page(page) -> str:
    try:
        page_dict = page.get_text("dict")
    except Exception:
        return ""

    spans = []
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            # skip vertical/rotated text, titles are horizontal
            dx, dy = line.get("dir", (1, 0))
            if abs(dy) > 0.1:
                continue
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                size = span.get("size", 0)
                if text:
                    spans.append((size, text))

    if not spans:
        return ""

    max_size = max(size for size, _ in spans)

    # collect only the largest-font spans, assumed to be the title
    title_parts = [text for size, text in spans if size >= max_size - 0.5]
    title = " ".join(title_parts).strip()
    title = re.sub(r"\s+", " ", title.replace("\xa0", " "))

    # sanity-check the guess: too short/long is probably not a real title
    word_count = len(title.split())
    if 2 <= word_count <= 25:
        return title
    return ""


def _extract_pdf_pages(path: Path) -> list[tuple[int, str, list[str]]]:
    try:
        import fitz
        doc = fitz.open(str(path))
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            tables = _extract_tables_pymupdf(page)
            pages.append((i + 1, text, tables))
            if (i + 1) % 50 == 0:
                print(f"    processed {i + 1}/{doc.page_count} pages...")
        doc.close()
        if any(t.strip() for _, t, _ in pages):
            return [(n, t, tabs) for n, t, tabs in pages if t.strip()]
    except Exception as e:
        print(f"  [warn] PyMuPDF failed on '{path.name}': {e}")

    # fall back to pdfplumber if pymupdf failed or found no text
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                tables = _extract_tables_pdfplumber(page)
                if page_text:
                    pages.append((i + 1, page_text, tables))
        if pages:
            return pages
    except Exception as e:
        print(f"  [warn] pdfplumber failed on '{path.name}': {e}")

    print(f"  [warn] No text could be extracted from '{path.name}' (likely a scanned/image-only PDF).")
    return []


def _extract_tables_pymupdf(page) -> list[str]:

    tables = []

    try:
        found = page.find_tables()
        for table in found:
            try:
                rows = table.extract()
            except Exception:
                rows = []
            table_text = _rows_to_text(rows)
            if table_text:
                tables.append(table_text)
    except Exception:
        pass

    # if pymupdf's table detector found nothing, try matching a "Table N" caption instead
    if not tables:
        caption_table = _extract_table_by_caption(page.get_text())
        if caption_table:
            tables.append(caption_table)

    return tables


def _extract_table_by_caption(text: str) -> str:
    match = re.search(r"Table\s*\d+\s+[A-Z]", text)
    if not match:
        return ""
    return text[match.start():].strip()


def _extract_tables_pdfplumber(page) -> list[str]:

    tables = []
    try:
        raw_tables = page.extract_tables()
        for rows in raw_tables:
            table_text = _rows_to_text(rows)
            if table_text:
                tables.append(table_text)
    except Exception:
        pass

    if not tables:
        try:
            caption_table = _extract_table_by_caption(page.extract_text() or "")
            if caption_table:
                tables.append(caption_table)
        except Exception:
            pass

    return tables


def _rows_to_text(rows) -> str:
    lines = []
    for row in rows or []:
        cells = [(cell or "").strip() for cell in row]
        if any(cells):
            lines.append(" | ".join(cells))
    return "\n".join(lines)


def clean_text(text: str) -> str:
    # Collapse runs of whitespace within a line, but keep paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    return [re.sub(r"\s+", " ", p).strip() for p in paragraphs if p.strip()]


def chunk_page_text(text: str) -> list[str]:

    text = clean_text(text)
    if not text:
        return []

    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks = []
    current = ""

    for para in paragraphs:
        # a paragraph bigger than the chunk size can't fit as-is, slice it directly
        if len(para) > CHUNK_SIZE:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_hard_slice(para))
            continue

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
    # fixed-size sliding window slice, used only for oversized paragraphs
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
    # prepend the tail of the previous chunk so context isn't lost at chunk boundaries
    if len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-CHUNK_OVERLAP:]
        overlapped.append(f"{prev_tail} {chunks[i]}".strip())
    return overlapped


def metadata_db_path(output_dir: str = VECTOR_STORE_DIR) -> str:
    return os.path.join(output_dir, METADATA_DB_NAME)


def init_metadata_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            source           TEXT PRIMARY KEY,
            title             TEXT,
            author            TEXT,
            subject           TEXT,
            creation_date     TEXT,
            creation_date_iso TEXT,
            page_count        INTEGER,
            title_guessed     INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def save_metadata_db(docs: list[dict], output_dir: str = VECTOR_STORE_DIR) -> None:
  
    os.makedirs(output_dir, exist_ok=True)
    db_path = metadata_db_path(output_dir)
    init_metadata_db(db_path)

    conn = sqlite3.connect(db_path)
    # clear out old rows first since this is a full rebuild not an incremental update
    conn.execute("DELETE FROM documents")
    for doc in docs:
        meta = doc.get("metadata", {})
        conn.execute(
            """
            INSERT INTO documents
                (source, title, author, subject, creation_date, creation_date_iso, page_count, title_guessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                title=excluded.title,
                author=excluded.author,
                subject=excluded.subject,
                creation_date=excluded.creation_date,
                creation_date_iso=excluded.creation_date_iso,
                page_count=excluded.page_count,
                title_guessed=excluded.title_guessed
            """,
            (
                doc["source"],
                meta.get("title"),
                meta.get("author"),
                meta.get("subject"),
                meta.get("creation_date"),
                meta.get("creation_date_iso"),
                meta.get("page_count"),
                int(bool(meta.get("title_guessed", False))),
            ),
        )
    conn.commit()
    conn.close()
    print(f"Document metadata saved to '{db_path}' ({len(docs)} document(s))")


def load_metadata_db(output_dir: str = VECTOR_STORE_DIR) -> dict:
    """Read the documents table back into {source: {field: value}}, for
    the retriever and the Streamlit sidebar to use without either of them
    needing to know any SQL."""
    db_path = metadata_db_path(output_dir)
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM documents").fetchall()
    conn.close()

    return {
        row["source"]: {
            "title": row["title"],
            "author": row["author"],
            "subject": row["subject"],
            "creation_date": row["creation_date"],
            "creation_date_iso": row["creation_date_iso"],
            "page_count": row["page_count"],
            "title_guessed": bool(row["title_guessed"]),
        }
        for row in rows
    }


def build_chunks(docs: list[dict]) -> list[dict]:
    all_chunks = []
    for doc in docs:
        chunk_idx = 0
        for page_num, page_text, tables in doc["pages"]:

            # tables are kept as their own whole chunks, not merged into the prose chunking
            for table_text in tables:
                all_chunks.append({
                    "id": f"{doc['source']}::chunk_{chunk_idx}",
                    "source": doc["source"],
                    "chunk_index": chunk_idx,
                    "page": page_num,
                    "text": table_text,
                    "is_table": True,
                })
                chunk_idx += 1

            pieces = chunk_page_text(page_text)
            for piece in pieces:
                all_chunks.append({
                    "id": f"{doc['source']}::chunk_{chunk_idx}",
                    "source": doc["source"],
                    "chunk_index": chunk_idx,
                    "page": page_num,
                    "text": piece,
                    "is_table": False,
                })
                chunk_idx += 1
    return all_chunks


def build_vector_store(chunks: list[dict], model_name: str = EMBEDDING_MODEL_NAME, 
                       output_dir: str = VECTOR_STORE_DIR, batch_size: int = EMBEDDING_BATCH_SIZE,
                       progress_callback=None) -> None:
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = [c["text"] for c in chunks]
    total = len(texts)
    print(f"Generating embeddings for {total} chunks")

    batch_embeddings = []
    for start in range(0, total, batch_size):
        batch_texts = texts[start:start + batch_size]
        # normalized embeddings let faiss's inner product act as cosine similarity
        batch_vectors = model.encode(batch_texts, convert_to_numpy=True, normalize_embeddings=True)
        batch_embeddings.append(batch_vectors)

        done = min(start + batch_size, total)
        if progress_callback:
            progress_callback(done, total)
        else:
            print(f"  embedded {done}/{total} chunks")

    embeddings = np.vstack(batch_embeddings).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(output_dir, "index.faiss"))
    # chunk text/metadata lives alongside the index since faiss only stores vectors
    with open(os.path.join(output_dir, "metadata.pkl"), "wb") as f:
        pickle.dump({"chunks": chunks, "model_name": model_name, "dimension": dimension}, f)

    print(f"Vector store saved to '{output_dir}' with {len(chunks)} chunks")


def main() -> None:
    print("Loading documents")
    docs = load_documents()
    print(f"Loaded {len(docs)} document(s)")

    print("Saving document metadata")
    save_metadata_db(docs)

    print("Splitting documents into chunks")
    chunks = build_chunks(docs)
    print(f"Created {len(chunks)} chunk(s)")

    build_vector_store(chunks)
    print("Done!")


if __name__ == "__main__":
    main()