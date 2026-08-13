# RAG for Tabular Data

## Overview

The RAG pipeline extracts structural metadata from each PDF, stores
it and uses it as part of retrieval alongside vector similarity so
that a question referencing a document by name, author, subject or
recency is matched against that metadata directly rather than relying
on semantic similarity alone.

## Tabular data (CSV, TSV, XLSX, XLS)

Standalone spreadsheet files are ingested the same way as PDF tables:
each one is read with pandas, converted to `header | cell | cell`
row text, and split into row-batched chunks (40 rows or ~3000
characters, whichever comes first) rather than embedded as one giant
blob. The column header is repeated at the top of every chunk so a
single retrieved chunk stays interpretable without the rest of the
table. Every chunk from a spreadsheet is flagged `is_table` the same
way an in-PDF table is, so it gets the same "table" badge in the UI.

- CSV: the delimiter (comma, semicolon, pipe, etc.) is auto-detected.
- TSV: read as tab-delimited.
- XLSX/XLS: every sheet is read and chunked separately; each chunk is
  prefixed with `Sheet: <name>` for context and the sheet number
  flows through the existing "page" field.
- XLSX workbook properties (title, author, subject, created date) are
  read the same way PDF metadata is so the title/author/subject
  boost and recency boost apply to spreadsheets too. CSV/TSV have no
  such embedded metadata so those fields stay empty for them.

## Metadata extraction

During indexing, each PDF's title, author, subject and creation date
are extracted. When a PDF's own embedded metadata does not have
these fields set, the title is detected from the largest bold or
largest-font text on the first page and the author is detected from
the line immediately following it filtered to exclude affiliation
and email-like text.

## Storage

Metadata is stored in `vector_store/metadata.db`, a SQLite database
with one row per document:

| Column        | Description                          |
|---------------|---------------------------------------|
| filename      | Document filename, primary key       |
| title         | Document title                       |
| author        | Document author                      |
| subject       | Subject or DOI field                 |
| creation_date | Document creation date, if present   |

Storing metadata once per document, separate from the chunk data,
keeps it queryable independently of the vector store and avoids
duplicating the same fields across every chunk of a document.

## Retrieval

Retrieval combines three signals to select the final chunks for a
question:

1. Semantic similarity from the vector store.
2. Keyword matching (BM25).
3. Metadata relevance, computed by tokenizing the question and
   comparing it against each document's title, author and subject,
   with the boost proportional to how many words overlap. A question
   that references a document by a partial or reworded title is still
   matched not only an exact filename or title match.

A recency signal is also applied: if a question implies wanting the
most recent version of something, documents are scored by how recent
their creation date is relative to the others in the retrieved pool,
and that score contributes to ranking as well. Documents without a
creation date receive no recency boost, positive or negative.

All three signals are combined before the final top-k chunks are
selected and passed to the language model for answer generation,
along with their metadata, so retrieval is not vector similarity
alone at any stage of the pipeline.

