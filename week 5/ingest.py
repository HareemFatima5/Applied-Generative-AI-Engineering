import os
import re
import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = "documents"
VECTOR_STORE_DIR = "vector_store"
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
            pages = [(None, text, [], "")] if text.strip() else []
            metadata = {"title": None, "author": None, "subject": None,
                        "creation_date": None, "page_count": None}
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


def _extract_pdf_metadata(path: Path) -> dict:
   
    metadata = {"title": None, "author": None, "subject": None,
                "creation_date": None, "page_count": None,
                "title_guessed": False, "author_guessed": False}
    try:
        import fitz
        doc = fitz.open(str(path))
        pdf_info = doc.metadata or {}
        metadata["title"] = pdf_info.get("title") or None
        metadata["author"] = pdf_info.get("author") or None
        metadata["subject"] = pdf_info.get("subject") or None
        metadata["creation_date"] = pdf_info.get("creationDate") or None
        metadata["page_count"] = doc.page_count

        if (not metadata["title"] or not metadata["author"]) and doc.page_count > 0:
            guessed_title, guessed_author = _guess_title_and_author_from_page(doc[0])
            if not metadata["title"] and guessed_title:
                metadata["title"] = guessed_title
                metadata["title_guessed"] = True
            if not metadata["author"] and guessed_author:
                metadata["author"] = guessed_author
                metadata["author_guessed"] = True

        doc.close()
    except Exception as e:
        print(f"  [warn] could not read metadata from '{path.name}': {e}")
    return metadata


AFFILIATION_KEYWORDS = (
    "university", "institute", "department", "dept", "school", "college",
    "laborator", "corp", "inc.", "ltd", "faculty", "technolog", "@",
    "http", "www.", "research", "brain",
)


def _guess_title_and_author_from_page(page) -> tuple:
   
    try:
        page_dict = page.get_text("dict")
    except Exception:
        return "", ""

    spans = []
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            dx, dy = line.get("dir", (1, 0))
            if abs(dy) > 0.1:
                continue
            bbox = line.get("bbox", (0, 0, 0, 0))
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                size = span.get("size", 0)
                if text:
                    spans.append((bbox[1], bbox[0], size, text))

    if not spans:
        return "", ""

    rows = _group_spans_into_rows(spans)
    title = _guess_title_from_rows(rows)
    author = _guess_author_from_rows(rows, title) if title else ""
    return title, author


def _group_spans_into_rows(spans, tolerance: float = 3.0) -> list[tuple]:
    """Spans on the same visual row (e.g. side-by-side author name columns)
    come back as separate lines from PyMuPDF since they're at different
    x-positions. Group anything within a few points of the same y-position
    into one row and join left to right, or a row of author names sitting
    in columns would otherwise only ever contribute its first column."""
    spans_sorted = sorted(spans, key=lambda s: (s[0], s[1]))
    rows = []
    current_row = []
    current_y = None
    for y0, x0, size, text in spans_sorted:
        if current_y is None or abs(y0 - current_y) <= tolerance:
            current_row.append((x0, size, text))
            current_y = current_y if current_y is not None else y0
        else:
            rows.append(current_row)
            current_row = [(x0, size, text)]
            current_y = y0
    if current_row:
        rows.append(current_row)

    result = []
    for row in rows:
        row.sort(key=lambda r: r[0])
        text = " ".join(t for _, _, t in row)
        max_size = max(s for _, s, _ in row)
        result.append((max_size, text))
    return result


def _guess_title_from_rows(rows: list[tuple]) -> str:
    if not rows:
        return ""
    max_size = max(size for size, _ in rows)
    title_parts = [text for size, text in rows if size >= max_size - 0.5]
    title = " ".join(title_parts).strip()
    title = re.sub(r"\s+", " ", title.replace("\xa0", " "))
    word_count = len(title.split())
    if 2 <= word_count <= 25:
        return title
    return ""


def _guess_author_from_rows(rows: list[tuple], title: str) -> str:
    for i, (size, text) in enumerate(rows):
        if text == title and i + 1 < len(rows):
            candidate = rows[i + 1][1]
            if _looks_like_author_row(candidate):
                return candidate
            return ""
    return ""


def _looks_like_author_row(text: str) -> bool:
    lowered = text.lower()
    if any(keyword in lowered for keyword in AFFILIATION_KEYWORDS):
        return False
    if any(ch.isdigit() for ch in text):
        return False
    words = text.split()
    return 2 <= len(words) <= 20


def _extract_pdf_pages(path: Path) -> list[tuple[int, str, list[str], str]]:

    try:
        import fitz
        doc = fitz.open(str(path))
        pages = []
        current_section = ""
        for i, page in enumerate(doc):
            text = page.get_text()
            tables = _extract_tables_pymupdf(page)
            heading = _extract_page_heading(page)
            if heading:
                current_section = heading
            pages.append((i + 1, text, tables, current_section))
            if (i + 1) % 50 == 0:
                print(f"    processed {i + 1}/{doc.page_count} pages...")
        doc.close()
        if any(t.strip() for _, t, _, _ in pages):
            return [(n, t, tabs, sec) for n, t, tabs, sec in pages if t.strip()]
    except Exception as e:
        print(f"  [warn] PyMuPDF failed on '{path.name}': {e}")

    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                tables = _extract_tables_pdfplumber(page)
                if page_text:
                    # pdfplumber's font/flag info isn't used here, so the
                    # fallback path doesn't attempt section detection.
                    pages.append((i + 1, page_text, tables, ""))
        if pages:
            return pages
    except Exception as e:
        print(f"  [warn] pdfplumber failed on '{path.name}': {e}")

    print(f"  [warn] No text could be extracted from '{path.name}' (likely a scanned/image-only PDF).")
    return []


def _extract_page_heading(page) -> str:
 
    try:
        page_dict = page.get_text("dict")
    except Exception:
        return ""

    body_size = _estimate_body_font_size(page_dict)
    bold_lines = []  # (y0, text, size)

    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            dx, dy = line.get("dir", (1, 0))
            if abs(dy) > 0.1:
                continue
            line_text = "".join(span.get("text", "") for span in line.get("spans", []))
            line_text = line_text.strip()
            if not line_text:
                continue
            is_bold = any(span.get("flags", 0) & 16 for span in line.get("spans", []))
            max_size = max((span.get("size", 0) for span in line.get("spans", [])), default=0)
            if is_bold and max_size >= body_size - 0.5:
                bbox = line.get("bbox", (0, 0, 0, 0))
                bold_lines.append((bbox[1], line_text, max_size))

    if not bold_lines:
        return ""

    heading_blocks = _merge_wrapped_lines(bold_lines)

    valid_headings = [
        text for text in heading_blocks
        if _looks_like_heading(text, body_size)
    ]
    if not valid_headings:
        return ""

    heading = re.sub(r"\s+", " ", valid_headings[-1].replace("\xa0", " ")).strip()
    return heading


def _estimate_body_font_size(page_dict) -> float:
    """Most common font size on the page, weighted by character count so a
    handful of large heading characters don't outweigh a full page of
    body text."""
    sizes = {}
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text:
                    size = round(span.get("size", 0), 1)
                    sizes[size] = sizes.get(size, 0) + len(text)
    if not sizes:
        return 10.0
    return max(sizes, key=sizes.get)


def _merge_wrapped_lines(bold_lines: list[tuple], gap_threshold: float = 16.0) -> list[str]:
    """Bold lines that sit close together vertically are one heading that
    wrapped across two physical lines, not two separate headings. Merge
    any lines whose gap is smaller than a typical line's own height."""
    if not bold_lines:
        return []

    blocks = []
    current_parts = [bold_lines[0][1]]
    prev_y = bold_lines[0][0]

    for y0, text, size in bold_lines[1:]:
        gap = y0 - prev_y
        if 0 <= gap <= gap_threshold:
            current_parts.append(text)
        else:
            blocks.append(" ".join(current_parts))
            current_parts = [text]
        prev_y = y0

    blocks.append(" ".join(current_parts))
    return blocks


_TRAILING_STOPWORDS = {
    "to", "with", "and", "of", "in", "on", "for", "by", "the", "a", "an",
    "from", "as", "at", "or", "that", "which", "is", "are", "regard",
}


def _looks_like_heading(text: str, body_size: float) -> bool:
    stripped = text.strip()
    # a bold running page number like "420" isn't a heading
    if stripped.isdigit():
        return False

    words = stripped.split()
    if not (1 <= len(words) <= 14):
        return False

    lowered = stripped.lower()
    if lowered.startswith(("fig", "table", "eq.", "eq ")):
        return False

    last_word = re.sub(r"[^a-z]", "", words[-1].lower())
    if last_word in _TRAILING_STOPWORDS:
        return False

    return True


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
    # (blank lines) intact so paragraph-based splitting below still works.
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
  
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + CHUNK_SIZE, length)
        chunks.append(text[start:end])
        start = end
    return chunks


def _add_overlap(chunks: list[str]) -> list[str]:

    if len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-CHUNK_OVERLAP:]
        overlapped.append(f"{prev_tail} {chunks[i]}".strip())
    return overlapped


def build_chunks(docs: list[dict]) -> list[dict]:
    all_chunks = []
    for doc in docs:
        chunk_idx = 0
        metadata = doc.get("metadata", {})
        for page_num, page_text, tables, section in doc["pages"]:
            for table_text in tables:
                all_chunks.append({
                    "id": f"{doc['source']}::chunk_{chunk_idx}",
                    "source": doc["source"],
                    "chunk_index": chunk_idx,
                    "page": page_num,
                    "section": section,
                    "text": table_text,
                    "is_table": True,
                    "title": metadata.get("title"),
                    "author": metadata.get("author"),
                    "subject": metadata.get("subject"),
                    "creation_date": metadata.get("creation_date"),
                    "page_count": metadata.get("page_count"),
                    "title_guessed": metadata.get("title_guessed", False),
                    "author_guessed": metadata.get("author_guessed", False),
                })
                chunk_idx += 1

            pieces = chunk_page_text(page_text)
            for piece in pieces:
                all_chunks.append({
                    "id": f"{doc['source']}::chunk_{chunk_idx}",
                    "source": doc["source"],
                    "chunk_index": chunk_idx,
                    "page": page_num,
                    "section": section,
                    "text": piece,
                    "is_table": False,
                    "title": metadata.get("title"),
                    "author": metadata.get("author"),
                    "subject": metadata.get("subject"),
                    "creation_date": metadata.get("creation_date"),
                    "page_count": metadata.get("page_count"),
                    "title_guessed": metadata.get("title_guessed", False),
                    "author_guessed": metadata.get("author_guessed", False),
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