# Ask My Documents

A RAG project I built to answer questions from my own PDFs instead of
scrolling through them manually. Upload a document, ask something in
plain English and get an answer along with the exact passages it came
from we you can actually check it's right instead of just trusting it.

![App screenshot](https://github.com/HareemFatima5/Applied-Generative-AI-Engineering/blob/main/week%204/image%201.PNG)

## How it works

1) First, documents get split into chunks and each chunk is embedded and
stored in a FAISS index along with which file and page it came from.

2) When we ask a question, it doesn't just do a plain embedding search.
It runs two searches at once, a semantic one using the embeddings and
a keyword one (BM25) because relying on embeddings alone missed exact
numbers and section titles more than I expected. Both sets of results
get combined and then reranked using a cross-encoder which is slower
but much better at telling which chunk actually answers the question
instead of just being loosely related to it.

3) Once the right chunks are found, they're passed to Gemini as context
and it writes the actual answer. If there's no API key set or the
Gemini call fails for some reason, it just falls back to showing the
top passage instead of breaking.

The Streamlit app wraps all of this so we don't need to touch the
command line at all, we can upload files, build the index and ask
questions from the browser.

## Project structure

```
ingest.py         loads and chunks documents, builds the vector store
retriever.py      retrieves the relevant chunks for a question
rag_answer.py     generates an answer from those chunks using Gemini
app.py            the Streamlit app
requirements.txt  packages needed to run everything
```

## Setup

```
pip install -r requirements.txt
```

If we want generated answers instead of just raw passages, we need to set our
Gemini key:

```
export GEMINI_API_KEY=our_key_here
```

It'll still work without this, it just won't generate a full answer.

## Running it

Command line version, put your files in a folder called `documents`
first:

```
python ingest.py
python rag_answer.py "what is the attendance policy"
```

Or just run the app:

```
streamlit run app.py
```

Upload documents, hit build index in the sidebar, and ask away.

## Explanation

Chunking splits on paragraph breaks instead of a fixed number of
characters. Cutting text at exactly 2000 characters sounds fine until
it slices a sentence in half right where the actual answer was.

The candidate pool size for retrieval scales with how big the document
is. A fixed number worked for a small handbook but completely missed
the right chunk on a much bigger one since it just never made it into
the pool being reranked.

Embedding model is all-MiniLM-L6-v2, reranking uses
cross-encoder/ms-marco-MiniLM-L-6-v2. The reranker only changes the
final ranking, it has nothing to do with how chunks are stored.
