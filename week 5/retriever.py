import os
import pickle
import re
from datetime import date

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

from ingest import load_metadata_db

VECTOR_STORE_DIR = "vector_store"
DEFAULT_TOP_K = 8

BASE_CANDIDATE_POOL_SIZE = 150
MAX_CANDIDATE_POOL_SIZE = 400

RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
METADATA_BOOST = 0.5
MIN_TOKEN_LENGTH = 3
RECENCY_BOOST = 0.4
RECENCY_KEYWORDS = {
    "latest", "newest", "most recent", "recent", "recently",
    "current", "currently", "up to date", "up-to-date", "updated",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9%]+", text.lower())


def _significant_tokens(text: str) -> set[str]:
    # drops noise tokens so metadata overlap isn't inflated by them
    return {t for t in _tokenize(text) if len(t) >= MIN_TOKEN_LENGTH}


def _query_wants_recency(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in RECENCY_KEYWORDS)


class Retriever:
    def __init__(self, vector_store_dir: str = VECTOR_STORE_DIR):
        index_path = os.path.join(vector_store_dir, "index.faiss")
        metadata_path = os.path.join(vector_store_dir, "metadata.pkl")

        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"No vector store found in '{vector_store_dir}'.")

        self.index = faiss.read_index(index_path)

        with open(metadata_path, "rb") as f:
            data = pickle.load(f)

        self.chunks = data["chunks"]
        self.model_name = data["model_name"] 
        self.model = SentenceTransformer(self.model_name)
        self.reranker = CrossEncoder(RERANK_MODEL_NAME)

        self.doc_metadata = load_metadata_db(vector_store_dir)

        # BM25 keyword index, built once over all chunks.
        tokenized_chunks = [_tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_chunks)

    def _pool_size(self) -> int:
        # scales the candidate pool with corpus size clamped between base and max
        total = len(self.chunks)
        return max(BASE_CANDIDATE_POOL_SIZE, min(MAX_CANDIDATE_POOL_SIZE, total // 10))

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
        """Return top_k chunks, ranked by cross-encoder relevance to the query."""
        pool_size = self._pool_size()

        semantic = self._semantic_candidates(query, pool_size=pool_size)
        keyword = self._keyword_candidates(query, pool_size=pool_size)

        candidates = self._merge(semantic, keyword)
        if not candidates:
            return []

        return self._rerank(query, candidates, top_k=top_k)

    def _semantic_candidates(self, query: str, pool_size: int) -> list[dict]:
        """FAISS ANN search - good for meaning/paraphrase matches."""
        query_vector = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")

        scores, indices = self.index.search(query_vector, pool_size)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            # faiss pads with -1 when fewer than pool_size vectors exist
            if idx == -1:
                continue
            results.append(self._to_candidate(idx, bi_encoder_score=float(score)))
        return results

    def _keyword_candidates(self, query: str, pool_size: int) -> list[dict]:
        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:pool_size]

        results = []
        for idx in top_indices:
            # indices are sorted descending so a zero score means the rest are zero too
            if scores[idx] <= 0:
                break
            results.append(self._to_candidate(int(idx), bm25_score=float(scores[idx])))
        return results

    def _to_candidate(self, idx: int, bi_encoder_score: float = None, bm25_score: float = None) -> dict:
        chunk = self.chunks[idx]
        doc_meta = self.doc_metadata.get(chunk["source"], {})
        return {
            "text": chunk["text"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "page": chunk.get("page"),
            "title": doc_meta.get("title"),
            "author": doc_meta.get("author"),
            "subject": doc_meta.get("subject"),
            "creation_date": doc_meta.get("creation_date"),
            "creation_date_iso": doc_meta.get("creation_date_iso"),
            "page_count": doc_meta.get("page_count"),
            "is_table": chunk.get("is_table", False),
            "bi_encoder_score": bi_encoder_score,
            "bm25_score": bm25_score,
        }

    def _merge(self, semantic: list[dict], keyword: list[dict]) -> list[dict]:
        """Union of both candidate sets, de-duplicated by chunk text."""
        merged = {}
        for c in semantic + keyword:
            key = c["text"]
            if key in merged:
                # keep whichever score(s) are present from either source
                merged[key]["bi_encoder_score"] = merged[key]["bi_encoder_score"] or c["bi_encoder_score"]
                merged[key]["bm25_score"] = merged[key]["bm25_score"] or c["bm25_score"]
            else:
                merged[key] = c
        return list(merged.values())

    def _rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        # cross-encoder scores query+passage pairs jointly, more accurate than bi-encoder similarity alone
        pairs = [[query, c["text"]] for c in candidates]
        rerank_scores = self.reranker.predict(pairs)

        for c, s in zip(candidates, rerank_scores):
            c["rerank_score"] = float(s)

        self._apply_metadata_boost(query, candidates)
        self._apply_recency_boost(query, candidates)

        for c in candidates:
            c["score"] = c["rerank_score"] + c["metadata_boost"] + c["recency_boost"]

        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:top_k]

    def _apply_metadata_boost(self, query: str, candidates: list[dict]) -> None:
        # rewards chunks whose filename/title/author/subject overlaps query terms,
        # e.g. asking about "smith report" should favor a doc authored by smith
        query_tokens = _significant_tokens(query)

        for c in candidates:
            boost = 0.0
            source_name = os.path.splitext(c["source"])[0]
            for field in (source_name, c.get("title"), c.get("author"), c.get("subject")):
                if not field or not query_tokens:
                    continue
                field_tokens = _significant_tokens(field)
                if not field_tokens:
                    continue
                overlap = field_tokens & query_tokens
                if overlap:
                    boost += METADATA_BOOST * (len(overlap) / len(field_tokens))
            c["metadata_boost"] = boost

    def _apply_recency_boost(self, query: str, candidates: list[dict]) -> None:
        # only kicks in for queries that explicitly ask for recent/current info
        if not _query_wants_recency(query):
            for c in candidates:
                c["recency_boost"] = 0.0
            return

        dated = []
        for c in candidates:
            iso = c.get("creation_date_iso")
            if not iso:
                c["recency_boost"] = 0.0
                continue
            try:
                c["_parsed_date"] = date.fromisoformat(iso)
                dated.append(c)
            except ValueError:
                c["recency_boost"] = 0.0

        if not dated:
            return

        # scale boost linearly across the observed date range in this candidate set so it's relative to what's actually retrieved rather than an absolute date
        oldest = min(c["_parsed_date"] for c in dated)
        newest = max(c["_parsed_date"] for c in dated)
        span_days = (newest - oldest).days

        for c in dated:
            if span_days == 0:
                c["recency_boost"] = RECENCY_BOOST
            else:
                fraction = (c["_parsed_date"] - oldest).days / span_days
                c["recency_boost"] = RECENCY_BOOST * fraction
            del c["_parsed_date"]


def main() -> None:
    retriever = Retriever()
    query = input("Enter a question: ").strip()
    if not query:
        print("No question entered.")
        return

    results = retriever.retrieve(query, top_k=8)
    if not results:
        print("No relevant chunks found.")
        return

    for i, r in enumerate(results, start=1):
        print(f"\nResult {i}  |  source: {r['source']}  |  score: {r['score']:.4f}")
        print(r["text"][:400])


if __name__ == "__main__":
    main()