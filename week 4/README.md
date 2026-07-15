# Document Retrieval

## Explanation

This is the retrieval part of the RAG project. It takes a folder of
documents, splits them into chunks, builds a vector store and lets us
search that vector store with a question.

## What I had on day 1

On day 1 I had a basic prototype working. It loaded PDF, txt and md
files, split the text into chunks of a fixed size (2000 characters,
with some overlap), embedded each chunk with a sentence embedding
model and stored the embeddings in a FAISS index. To answer a query,
it embedded the question and pulled back the chunks with the closest
embeddings.

## Why it did not work well

When I tested this on actual documents (university handbooks), the
retrieval quality was poor. Asking a direct question like what the
attendance policy is would return chunks from unrelated sections
instead of the section that actually had the answer.

Looking into it, there were two problems.

1) The first was chunking. Splitting text every 2000 characters does not
care where a sentence or paragraph ends so a chunk could start or end
in the middle of a sentence, or mix the end of one topic with the
start of a completely different one. This meant the specific
information I was searching for could be split across chunk
boundaries, or diluted inside a chunk that was mostly about something
else so its embedding no longer matched the question well.

2) The second was that similarity search on embeddings alone is not
always precise enough. It ranks chunks by how close their meaning is
to the question, but it does not look at the query and a chunk
together so a chunk that only vaguely relates to the topic can end up
ranked above the chunk that actually answers it. This was worse for
larger documents since there were simply more chunks competing for
the same few results.

## What I changed on day 2

To fix the chunking problem, I rewrote the chunking so it splits text
on paragraph boundaries instead of a fixed character count and keeps
track of which page each chunk came from. A single paragraph that is
still too long gets split on its own so it does not pull unrelated
text in with it.

To fix the ranking problem, I added a second stage after the initial
search. Instead of only using the embedding search, retrieval now
pulls a batch of candidate chunks from two sources at once: the
embedding search and a keyword based search (BM25) that looks for the
exact words in the question. This is useful because a keyword search
will catch things like an exact number or a section title even if its
embedding was not a strong match. The candidates from both are then
passed through a cross-encoder model which looks at the question and
each chunk together and re-scores them and only the top results after
this re-scoring are returned. I also made the number of candidates
scale with how many chunks a document has since a fixed number was
not enough once I tested on a much larger handbook.

## Files

ingest.py
Loads pdf files from the documents folder splits the text
into chunks and builds a FAISS index with sentence embeddings.

retriever.py
Loads the FAISS index and answers a query by combining semantic search
and keyword search, then reranking the combined results with a
cross-encoder for better accuracy.

requirements.txt
Python packages needed to run the scripts.

## How to run

1. Install the requirements

   pip install -r requirements.txt

2. Put your documents in a folder named documents

3. Build the index

   python ingest.py

4. Search the index

   python retriever.py

   You will be asked to type a question and it will print the top
   matching chunks along with their source file, page number and score.
