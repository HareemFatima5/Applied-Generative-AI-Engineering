import os
import pickle
import re

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

VECTOR_STORE_DIR = "vector_store"
DEFAULT_TOP_K = 8

BASE_CANDIDATE_POOL_SIZE = 150
MAX_CANDIDATE_POOL_SIZE = 400

RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9%]+", text.lower())


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

        tokenized_chunks = [_tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_chunks)

    def _pool_size(self) -> int:
        "Dynamic retrieval"
        total = len(self.chunks)
        return max(BASE_CANDIDATE_POOL_SIZE, min(MAX_CANDIDATE_POOL_SIZE, total // 10))

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
        pool_size = self._pool_size()

        semantic = self._semantic_candidates(query, pool_size=pool_size)
        keyword = self._keyword_candidates(query, pool_size=pool_size)

        candidates = self._merge(semantic, keyword)
        if not candidates:
            return []

        return self._rerank(query, candidates, top_k=top_k)

    def _semantic_candidates(self, query: str, pool_size: int) -> list[dict]:
        query_vector = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")

        scores, indices = self.index.search(query_vector, pool_size)

        results = []
        for score, idx in zip(scores[0], indices[0]):
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
            if scores[idx] <= 0:
                break
            results.append(self._to_candidate(int(idx), bm25_score=float(scores[idx])))
        return results

    def _to_candidate(self, idx: int, bi_encoder_score: float = None, bm25_score: float = None) -> dict:
        chunk = self.chunks[idx]
        return {
            "text": chunk["text"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "page": chunk.get("page"),
            "bi_encoder_score": bi_encoder_score,
            "bm25_score": bm25_score,
        }

    def _merge(self, semantic: list[dict], keyword: list[dict]) -> list[dict]:
        merged = {}
        for c in semantic + keyword:
            key = c["text"]
            if key in merged:
                merged[key]["bi_encoder_score"] = merged[key]["bi_encoder_score"] or c["bi_encoder_score"]
                merged[key]["bm25_score"] = merged[key]["bm25_score"] or c["bm25_score"]
            else:
                merged[key] = c
        return list(merged.values())

    def _rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        pairs = [[query, c["text"]] for c in candidates]
        rerank_scores = self.reranker.predict(pairs)

        for c, s in zip(candidates, rerank_scores):
            c["score"] = float(s)

        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:top_k]


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
