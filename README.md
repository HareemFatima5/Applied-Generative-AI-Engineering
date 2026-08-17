# Applied Generative AI Engineering Internship (8 Weeks)

This repository documents the work completed during an 8-week Applied Generative AI Engineering internship at RolusTech covering GenAI application development, prompt engineering, applied ML/NLP, model fine-tuning and retrieval-augmented generation over documents and tabular data.

## Roadmap

### Week 1: AI Weather App
A Streamlit app where Gemini orchestrates weather API calls through function calling rather than a fixed request flow. The LLM extracts the city from the user's query, decides when to call the `fetch_weather` tool, pulls live data from OpenWeatherMap and formats the response with practical advice.

### Week 2: Prompt Engineering
Practical work on prompting techniques: zero-shot, few-shot, role-based prompting, output constraints and hallucination control. Applied to summarization, classification, entity/keyword extraction and structured JSON generation, with prompt versions tracked and compared.

### Week 3: NLP and Text Classification
Core ML and NLP workflow: preprocessing (tokenization, stop words, stemming vs. lemmatization), vectorization (Bag of Words, TF-IDF, embeddings) and four classifiers trained across different datasets — Logistic Regression on IMDB sentiment, Naive Bayes on SMS spam, Random Forest on spam and BBC News and SVM on 20 Newsgroups. Evaluated with accuracy, precision, recall, F1 and confusion matrices comparing behavior across balanced/imbalanced and binary/multi-class settings.

### Week 4: Ask My Documents (RAG Basics)
A RAG pipeline for answering questions from uploaded PDFs with source passages attached. Documents are chunked and embedded into a FAISS index alongside file/page metadata. Retrieval runs semantic search and BM25 in parallel, merges the results and reranks with a cross-encoder before passing the top chunks to Gemini for answer generation falling back to raw passages if no API key is set. Wrapped in a Streamlit app for upload, indexing and querying.

### Week 5: PDF Metadata Extraction and Matching
Extends the RAG pipeline with structural metadata extraction — title, author, subject and creation date pulled from embedded PDF metadata or inferred from page layout when missing. Metadata is stored in a SQLite database (`vector_store/metadata.db`), separate from chunk data, and folded into retrieval as a third signal alongside vector similarity and BM25: token-overlap scoring against title/author/subject plus a recency boost when a question implies wanting the latest version of something.

### Week 6: *(not yet documented)*

### Week 7: Clickbait Headline Detector
Fine-tunes `distilbert-base-uncased` on the `christinacdl/clickbait_detection_dataset` (37.9k labeled headlines) for binary clickbait classification. Includes a training script with early stopping on validation F1, a `ClickbaitPredictor` class for inference and a Streamlit UI supporting both single-headline checks and batch CSV scoring.

### Week 8: RAG for Tabular Data 
Extends the document RAG pipeline with full support for tabular data — CSV, TSV, XLSX, and XLS. Spreadsheets are read with pandas and row-batched into chunks (40 rows or ~3000 characters) with the header repeated in every chunk, tagged `is_table` for consistent UI treatment alongside in-PDF tables. XLSX workbook metadata feeds the same title/author/subject and recency boosts used for PDFs. Combines semantic similarity, BM25 and metadata relevance into a single retrieval pipeline that generates answers with source attribution across mixed document and tabular corpora.

## Repository Structure
```
.
├── week-1-genai-foundations/
├── week-2-prompt-engineering/
├── week-3-applied-ml-nlp/
├── week-4-rag-basics/
├── week-5-rag-metadata/
├── week-6/
├── week-7-clickbait-detector/
└── week-8-rag-tabular-date/
```
