"""Streamlit web UI for the handbook RAG chatbot (Task 4).

Run:  streamlit run app.py
"""

import time
from dataclasses import replace
from datetime import datetime

import streamlit as st

from rag import RAGPipeline, Settings, list_ollama_models

st.set_page_config(page_title="CS Handbook Assistant", page_icon="🎓", layout="wide")

EXAMPLES = [
    "What courses are required for the Computer Science major?",
    "What are the learning outcomes of the CS program?",
    "How many credits do I need to complete the CS major?",
    "Can I do a minor in Computer Science? What does it require?",
]

BASE = Settings()


@st.cache_resource(show_spinner="Loading the document index (first run embeds the PDF)...")
def get_pipeline(chunk_size: int, chunk_overlap: int, rebuild_token: int) -> RAGPipeline:
    s = replace(BASE, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return RAGPipeline(s, rebuild=rebuild_token > 0, verbose=True)


def init_state():
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("rebuild_token", 0)


def render_sources(sources, low_conf):
    if not sources:
        return
    label = "Sources" + (" - low confidence" if low_conf else "")
    with st.expander(label, expanded=False):
        for s in sources:
            st.markdown(f"**{s['label']}** · similarity `{s['score']:.3f}`")
            st.caption(s["content"][:700] + ("..." if len(s["content"]) > 700 else ""))


def chat_as_markdown(messages) -> str:
    out = [f"# Chat export - {datetime.now():%Y-%m-%d %H:%M}\n"]
    for m in messages:
        out.append(f"**{'You' if m['role'] == 'user' else 'Assistant'}:** {m['content']}\n")
        for s in m.get("sources", [])[:3]:
            out.append(f"- source: {s['label']} (score {s['score']:.3f})")
        out.append("")
    return "\n".join(out)


init_state()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Settings")
    available = list_ollama_models(BASE.ollama_url)
    llms = [m for m in available if "embed" not in m] or [BASE.llm_model]
    default_idx = llms.index(BASE.llm_model) if BASE.llm_model in llms else 0
    model = st.selectbox("Language model", llms, index=default_idx)
    if not available:
        st.error(f"Cannot reach Ollama at {BASE.ollama_url}. Is it running?")

    top_k = st.slider("Chunks to retrieve (top-k)", 1, 10, BASE.top_k)
    temperature = st.slider("Temperature", 0.0, 1.0, BASE.temperature, 0.05)
    strict = st.toggle("Answer only from the handbook", value=BASE.prompt_mode == "strict",
                       help="Off = baseline behaviour: fall back to the model's own knowledge.")

    with st.expander("Indexing"):
        chunk_size = st.number_input("Chunk size (chars)", 200, 4000, BASE.chunk_size, 100)
        chunk_overlap = st.number_input("Chunk overlap (chars)", 0, 1000, BASE.chunk_overlap, 50)
        if st.button("Rebuild index"):
            st.session_state.rebuild_token += 1
            get_pipeline.clear()

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    c2.download_button("Export", chat_as_markdown(st.session_state.messages),
                       file_name="chat.md", use_container_width=True,
                       disabled=not st.session_state.messages)

try:
    rag = get_pipeline(int(chunk_size), int(chunk_overlap), st.session_state.rebuild_token)
except Exception as e:  # Ollama down, model not pulled, etc.
    st.error(f"Could not load the RAG pipeline: {e}")
    st.stop()

with st.sidebar:
    stats = rag.stats()
    st.caption(f"📄 {', '.join(stats['files'])}  \n🧩 {stats['chunks']} chunks · embed `{BASE.embed_model}`")

# -------------------------------------------------------------------- main
st.title("🎓 CS Major Handbook Assistant")
st.caption("Ask about program requirements, courses, learning outcomes and academic policies. "
           "Runs fully locally with Ollama + ChromaDB.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            render_sources(m.get("sources", []), m.get("low_conf", False))
            if m.get("meta"):
                st.caption(m["meta"])

pending = None
if not st.session_state.messages:
    st.markdown("**Try one of these:**")
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        if cols[i % 2].button(ex, use_container_width=True, key=f"ex{i}"):
            pending = ex

question = st.chat_input("Ask a question about the handbook...") or pending

if question:
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching the handbook..."):
                prepared = rag.prepare(question, history, top_k=top_k,
                                       prompt_mode="strict" if strict else "open", model=model)
            t0 = time.perf_counter()
            answer = st.write_stream(rag.stream(prepared, model=model, temperature=temperature))
            gen_s = time.perf_counter() - t0
        except Exception as e:
            answer, gen_s = f"⚠️ Error while generating an answer: {e}", 0.0
            prepared = None
            st.markdown(answer)

        sources = [{"label": s.label, "score": s.score, "content": s.content}
                   for s in (prepared.sources if prepared else [])]
        low_conf = bool(prepared and prepared.low_confidence)
        meta = (f"{model} · retrieval {prepared.retrieval_seconds:.2f}s · generation {gen_s:.1f}s"
                if prepared else "")
        if prepared and prepared.search_query != question:
            meta += f"  \n🔎 searched as: *{prepared.search_query}*"
        render_sources(sources, low_conf)
        if meta:
            st.caption(meta)

    st.session_state.messages.append({
        "role": "assistant", "content": answer if isinstance(answer, str) else str(answer),
        "sources": sources, "low_conf": low_conf, "meta": meta,
    })
    st.rerun()   # redraw from history so the example buttons disappear
