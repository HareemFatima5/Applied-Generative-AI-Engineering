import os
import argparse

from dotenv import load_dotenv
from retriever import Retriever, DEFAULT_TOP_K

load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GENERATION_MODEL = os.environ.get("GEMINI_GENERATION_MODEL", "gemini-3.1-flash-lite")
SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using only the "
    "provided context. If the answer is not contained in the context, "
    "say you don't have enough information."
)


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        page = chunk.get("page")
        location = f"{chunk['source']} (page {page})" if page else chunk["source"]
        parts.append(f"[{i}] Source: {location}\n{chunk['text']}")
    return "\n\n".join(parts)


def generate_with_gemini(question: str, context: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=GENERATION_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    response = model.generate_content(user_prompt, generation_config={"temperature": 0.2})
    return response.text.strip()


def generate_fallback(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant context found."
    return f"Most relevant passage:\n\n{chunks[0]['text']}"


def answer_question(question: str, top_k: int = DEFAULT_TOP_K, retriever: Retriever = None) -> dict:
    if retriever is None:
        retriever = Retriever()

    chunks = retriever.retrieve(question, top_k=top_k)
    context = build_context(chunks)

    api_key = os.environ.get("GEMINI_API_KEY")
    if GEMINI_AVAILABLE and api_key:
        try:
            answer = generate_with_gemini(question, context, api_key)
        except Exception as e:
            answer = f"Gemini API call failed ({e}). Showing the most relevant passage instead.\n\n{generate_fallback(chunks)}"
    else:
        answer = generate_fallback(chunks)

    return {"question": question, "answer": answer, "sources": chunks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="*", help="Question to ask")
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()

    question = " ".join(args.question).strip()
    if not question:
        question = input("Enter your question: ").strip()

    if not question:
        print("No question entered.")
        return

    result = answer_question(question, top_k=args.top_k)

    print("\nQuestion:", result["question"])
    print("\nAnswer:\n", result["answer"])
    print("\nSources used:")
    for chunk in result["sources"]:
        page_info = f", page {chunk['page']}" if chunk.get("page") else ""
        print(f"- {chunk['source']} (chunk {chunk['chunk_index']}{page_info}, score {chunk['score']:.4f})")


if __name__ == "__main__":
    main()
