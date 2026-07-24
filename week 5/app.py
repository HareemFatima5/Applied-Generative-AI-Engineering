import os
import shutil
import time

import streamlit as st

from ingest import (
    load_documents, build_chunks, build_vector_store, save_metadata_db, load_metadata_db,
    DOCUMENTS_DIR, VECTOR_STORE_DIR,
)
from retriever import Retriever, DEFAULT_TOP_K
from rag_answer import answer_question

# page configuration
st.set_page_config(
    page_title="Ask My Documents",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded",
)

# custom css styling
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ink:      #241F1A;
    --ink-soft: #6B6259;
    --paper:    #F6F1E7;
    --accent:   #E3A62F;
    --accent-soft: rgba(227, 166, 47, 0.16);
    --answer-bg: #FFFDF8;
    --rule:     #E7DFCF;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: var(--paper);
    color: var(--ink);
}

section[data-testid="stSidebar"] {
    background: var(--paper);
    border-right: 1px solid var(--rule);
}

section[data-testid="stSidebar"] * {
    color: var(--ink) !important;
}

/* hero section */
.hero {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 4px;
}

.hero-badge {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
}

.hero-title {
    font-weight: 800;
    font-size: 2.1rem;
    line-height: 1.12;
    color: var(--ink);
    margin: 0;
}

.hero-sub {
    color: var(--ink-soft);
    font-size: 0.98rem;
    margin: 10px 0 28px 0;
}

/* section labels */
.section-label {
    font-weight: 600;
    font-size: 0.82rem;
    color: var(--ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 26px 0 10px 0;
}

/* answer card */
.answer-card {
    background: var(--answer-bg);
    border-radius: 14px;
    padding: 22px 24px;
    margin-top: 8px;
    font-size: 1.05rem;
    line-height: 1.6;
    color: var(--ink);
    border: 1px solid var(--rule);
}

/* source rows */
.source-row {
    padding: 12px 0;
    border-bottom: 1px solid var(--rule);
}

.source-row:last-child {
    border-bottom: none;
}

.source-meta {
    font-size: 0.78rem;
    color: var(--accent);
    font-weight: 600;
    margin-bottom: 4px;
}

.source-text {
    font-size: 0.9rem;
    color: var(--ink-soft);
    line-height: 1.55;
}

.doc-meta {
    font-size: 0.76rem;
    color: var(--ink-soft);
    margin: -2px 0 8px 0;
    line-height: 1.5;
}

.boost-tag {
    display: inline-block;
    font-size: 0.72rem;
    color: var(--accent);
    font-weight: 600;
    margin-left: 6px;
}

/* buttons */
.stButton > button {
    background: var(--ink);
    color: var(--paper) !important;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.3rem;
    font-weight: 600;
}

.stButton > button:hover {
    background: var(--accent);
    color: var(--ink) !important;
}

.stTextInput > div > div > input {
    border-radius: 8px;
    border: 1px solid var(--rule);
    padding: 0.6rem 0.8rem;
}

.stProgress > div > div > div > div {
    background-color: var(--accent);
}

[data-testid="stFileUploaderDropzone"] {
    background: var(--answer-bg);
    border: 1px dashed var(--rule);
    border-radius: 10px;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# cache the retriever so it isn't rebuilt on every rerun
@st.cache_resource(show_spinner=False)
def load_retriever():
    return Retriever()

def load_document_metadata() -> dict:
    return load_metadata_db(VECTOR_STORE_DIR)

def render_hero():
    """Render the hero section with title and subtitle."""
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">&#128269;</div>
            <p class="hero-title">Ask your documents anything</p>
        </div>
        <p class="hero-sub">Upload files, then ask a question and get an answer grounded in what they actually say.</p>
        """,
        unsafe_allow_html=True,
    )

def render_sidebar(vector_store_ready: bool):
    """Render the sidebar with status and configuration options."""
    with st.sidebar:
        st.markdown("**Index status**")
        st.caption("Ready" if vector_store_ready else "Not built yet")

        top_k = st.slider(
            "Chunks to retrieve", min_value=1, max_value=10, value=DEFAULT_TOP_K,
            help="How many passages to pull before answering.",
        )

        show_sources = st.checkbox("Show retrieved sources", value=True)

        st.markdown("**Generation**")
        # only checks for the key's presence, not whether it's actually valid
        api_key_present = bool(os.environ.get("GEMINI_API_KEY"))
        st.caption(
            "Connected" if api_key_present
            else "No API key set, returning top passage only"
        )

        st.markdown("**Documents indexed**")
        if os.path.isdir(DOCUMENTS_DIR):
            files = sorted(os.listdir(DOCUMENTS_DIR))
            # avoid hitting the metadata db if there's no index to read from yet
            doc_metadata = load_document_metadata() if vector_store_ready else {}
            if files:
                for f in files:
                    meta = doc_metadata.get(f, {})
                    page_count = meta.get("page_count")
                    label = f"{f} ({page_count} pages)" if page_count else f
                    has_details = any(meta.get(k) for k in ("title", "author", "subject"))

                    with st.expander(label, expanded=False):
                        if meta.get("title"):
                            # title_label is unused beyond this, both branches give "Title"
                            title_label = "Title" if meta.get("title_guessed") else "Title"
                            st.caption(f"{title_label}: {meta['title']}")
                        if meta.get("author"):
                            st.caption(f"Author: {meta['author']}")
                        if meta.get("subject"):
                            st.caption(f"Subject: {meta['subject']}")
                        if not has_details:
                            st.caption("No title/author metadata found in this file.")
            else:
                st.caption("None yet")

    return top_k, show_sources

def save_uploaded_files(uploaded_files, replace_existing: bool) -> int:
    if replace_existing and os.path.isdir(DOCUMENTS_DIR):
        shutil.rmtree(DOCUMENTS_DIR)
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)

    saved = 0
    for uploaded in uploaded_files:
        target_path = os.path.join(DOCUMENTS_DIR, uploaded.name)
        with open(target_path, "wb") as f:
            f.write(uploaded.getbuffer())
        saved += 1
    return saved

def build_index_in_app(progress_callback=None) -> int:
    # rebuild the vector store from scratch each time
    if os.path.isdir(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)

    docs = load_documents(DOCUMENTS_DIR)
    save_metadata_db(docs, output_dir=VECTOR_STORE_DIR)
    chunks = build_chunks(docs)
    build_vector_store(chunks, output_dir=VECTOR_STORE_DIR, progress_callback=progress_callback)
    return len(chunks)

def render_upload_section():
    """Render the document upload and indexing section."""
    st.markdown('<div class="section-label">Upload documents</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        label="Upload documents",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        replace_existing = st.checkbox(
            "Replace existing documents",
            value=True,
            help="Uncheck to add these files to whatever is already indexed.",
        )
    with col_b:
        build_clicked = st.button("Build index", use_container_width=True)

    if build_clicked:
        if not uploaded_files:
            st.warning("Upload at least one .txt, .md, or .pdf file first.")
        else:
            status_text = st.empty()
            progress_bar = st.progress(0)

            status_text.caption("Saving uploaded files...")
            saved = save_uploaded_files(uploaded_files, replace_existing)

            status_text.caption("Splitting into chunks and embedding...")

            def update_progress(done: int, total: int) -> None:
                fraction = done / total if total else 0.0
                progress_bar.progress(min(fraction, 1.0))
                status_text.caption(f"Embedding chunk {done} of {total}...")

            try:
                num_chunks = build_index_in_app(progress_callback=update_progress)
            except Exception as e:
                status_text.empty()
                progress_bar.empty()
                st.error(f"Indexing failed: {e}")
                return

            progress_bar.progress(1.0)
            status_text.empty()
            progress_bar.empty()

            # drop the cached retriever so the next query picks up the new index
            load_retriever.clear()
            st.success(f"Indexed {saved} document(s) into {num_chunks} chunk(s).")

def render_answer(result: dict):
    """Render the answer from the RAG system."""
    st.markdown('<div class="section-label">Answer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer-card">{result["answer"]}</div>', unsafe_allow_html=True)

def render_sources(result: dict):
    """Render the source passages that were retrieved."""
    st.markdown('<div class="section-label">Retrieved passages</div>', unsafe_allow_html=True)

    if not result["sources"]:
        st.caption("No passages were retrieved for this question.")
        return

    for chunk in result["sources"]:
        page_info = f" · p.{chunk['page']}" if chunk.get("page") else ""

        extra_meta = []
        if chunk.get("title"):
            extra_meta.append(chunk["title"])
        if chunk.get("author"):
            extra_meta.append(chunk["author"])
        if chunk.get("subject"):
            extra_meta.append(chunk["subject"])
        if chunk.get("creation_date_iso"):
            extra_meta.append(f"dated {chunk['creation_date_iso']}")
        meta_info = f" · {' / '.join(extra_meta)}" if extra_meta else ""

        boost_tag = ""
        if chunk.get("metadata_boost"):
            boost_tag = '<span class="boost-tag">matched metadata</span>'
        if chunk.get("is_table"):
            boost_tag += '<span class="boost-tag">table</span>'

        preview = chunk["text"][:300] + ("..." if len(chunk["text"]) > 300 else "")
        st.markdown(
            f"""
            <div class="source-row">
                <div class="source-meta">{chunk['source']}{page_info}{meta_info} &middot; score {chunk['score']:.2f}{boost_tag}</div>
                <div class="source-text">{preview}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def main():
    """Main application entry point."""
    render_hero()
    render_upload_section()

    vector_store_ready = os.path.exists(os.path.join(VECTOR_STORE_DIR, "index.faiss"))
    top_k, show_sources = render_sidebar(vector_store_ready)

    st.markdown('<div class="section-label">Ask a question</div>', unsafe_allow_html=True)

    question = st.text_input(
        label="Question",
        placeholder="e.g. What is the attendance policy?",
        label_visibility="collapsed",
    )
    ask_clicked = st.button("Ask")

    if ask_clicked:
        if not vector_store_ready:
            st.error("No index found yet. Upload documents above and build the index first.")
            return

        if not question.strip():
            st.warning("Enter a question before asking.")
            return

        with st.spinner("Searching and drafting an answer..."):
            retriever = load_retriever()
            start = time.time()
            result = answer_question(question.strip(), top_k=top_k, retriever=retriever)
            elapsed = time.time() - start

        render_answer(result)
        st.caption(f"Answered in {elapsed:.2f}s using {len(result['sources'])} retrieved chunk(s).")

        if show_sources:
            render_sources(result)

if __name__ == "__main__":
    main()