# Document Retrieval and Answer Generation

## What this is

This adds answer generation on top of the retrieval from day 2. Instead
of just returning matching chunks, it now takes those chunks and asks
Gemini to write an answer to the question based on them.

## What I had on day 2

By day 2, retrieval was returning the correct chunks for a question
combining embedding search and keyword search and reranking the
results with a cross-encoder. What it did not do yet was turn those
chunks into an actual answer, it only returned the raw text.

## What I added on day 3

rag_answer.py takes a question, calls the retriever from day 2 to get
the relevant chunks and passes them as context to the Gemini API along
with the question asking it to answer using only that context. If the
answer is not in the context, it is told to say it does not have
enough information rather than guessing.

If no Gemini API key is set or the API call fails for any reason, it
falls back to returning the single most relevant chunk instead of
generating an answer so the tool still gives a usable result rather
than an error.

## Files

retriever.py
Same retriever from day 2, needed here since rag_answer.py depends on
it directly.

rag_answer.py
Retrieves relevant chunks for a question and generates an answer from
them using Gemini with a fallback to the top passage if Gemini is not
available.

requirements.txt
Python packages needed to run the scripts.

## How to run

1. Install the requirements

   pip install -r requirements.txt

2. Set your Gemini API key as an environment variable

   export GEMINI_API_KEY=your_key_here

3. Build the index first if you have not already (see day 2)

   python ingest.py

4. Ask a question

   python rag_answer.py "what is the attendance policy"

   This prints the generated answer along with the sources used to
   produce it. If no API key is set, it prints the most relevant
   passage instead of a generated answer.
