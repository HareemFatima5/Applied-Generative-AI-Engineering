# PDF Metadata Extraction and Matching

## Overview

The RAG pipeline extracts structural metadata from each PDF, stores
it and uses it as part of retrieval alongside vector similarity so
that a question referencing a document by name, author, subject or
recency is matched against that metadata directly rather than relying
on semantic similarity alone.

## Metadata extraction

During indexing, each PDF's title, author, subject, and creation date
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

