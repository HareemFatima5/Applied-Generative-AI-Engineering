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

GENERATION_MODEL = os.environ.get("GEMINI_GENERATION_MODEL", "gemini-3.1-flash-lite-preview")

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using only the "
    "provided context from the user's own documents. If the answer is not "
    "contained in the context, say clearly that you do not have enough "
    "information rather than guessing. When possible, mention which source "
    "document supports each part of your answer."
)


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[{i}] Source: {chunk['source']}\n{chunk['text']}")
    return "\n\n".join(parts)


def generate_with_gemini(question: str, context: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=GENERATION_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    response = model.generate_content(
        user_prompt,
        generation_config={"temperature": 0.2},
    )
    return response.text.strip()


def generate_fallback(chunks: list[dict]) -> str:
    """Used when no LLM API key is available, so the pipeline still works."""
    if not chunks:
        return "No relevant context was found in the indexed documents."
    best = chunks[0]
    return (
        "No language model API key was configured, so here is the most "
        f"relevant passage found instead (source: {best['source']}):\n\n{best['text']}"
    )


def answer_question(question: str, top_k: int = DEFAULT_TOP_K, retriever: Retriever = None) -> dict:
    """Run the full RAG pipeline for a single question and return the result."""
    if retriever is None:
        retriever = Retriever()

    chunks = retriever.retrieve(question, top_k=top_k)
    context = build_context(chunks)

    api_key = os.environ.get("GEMINI_API_KEY")
    if GEMINI_AVAILABLE and api_key:
        answer = generate_with_gemini(question, context, api_key)
    else:
        answer = generate_fallback(chunks)

    return {
        "question": question,
        "answer": answer,
        "sources": chunks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask My Documents: a basic RAG question answerer")
    parser.add_argument("question", nargs="*", help="Question to ask about your documents")
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve")
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
        print(f"- {chunk['source']} (chunk {chunk['chunk_index']}, score {chunk['score']:.4f})")


if __name__ == "__main__":
    main()