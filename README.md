# Local RAG Chatbot for the FUV Computer Science Major Handbook

A fully local Retrieval-Augmented Generation (RAG) system that answers questions about the
Fulbright University Vietnam **Computer Science Major Handbook**. It runs entirely on your own
machine using **Ollama** (LLM + embeddings), **ChromaDB** (vector store), **LangChain**, and a
**Streamlit** web UI, packaged with **Docker**.

CS311 Advanced Deep Learning, Fall 2026, Final Project.

```
           ┌──────────┐   pypdf    ┌──────────┐  nomic-embed-text  ┌──────────┐
 PDF/TXT ─►│  Loader  │──pages────►│ Splitter │──────chunks───────►│ ChromaDB │
           └──────────┘            └──────────┘                    └────┬─────┘
                                                                        │ top-k (cosine)
 Question ─────────────────────── embed query ──────────────────────────┤
                                                                        ▼
                                          ┌────────────────┐     ┌────────────┐
                    Streamlit UI / CLI ◄──│ qwen2.5 (Ollama)│◄────│   Prompt   │
                                          └────────────────┘     └────────────┘
```

## Features

| Task | What it covers | Where |
|---|---|---|
| 1. PDF support | Page-by-page PDF text extraction with page numbers, text cleaning, warnings for pages that would need OCR, `.txt` still supported | [`source_code/rag/loaders.py`](source_code/rag/loaders.py) |
| 2. Handbook chatbot | Grounded prompt with page citations, cosine retrieval, nomic task prefixes, a test question set and an evaluation script that compares models | [`source_code/rag/pipeline.py`](source_code/rag/pipeline.py), [`source_code/evaluate.py`](source_code/evaluate.py) |
| 3. Docker | App image plus a Compose stack with Ollama and automatic model download, mounted documents, persisted vector store, optional GPU | [`docker/`](docker/) |
| 4. Web UI | Streamlit chat with history, streaming answers, source viewer, model/top-k/temperature controls and chat export | [`source_code/app.py`](source_code/app.py) |

## Repository layout

```
├── source_code/
│   ├── rag/                  # config, loaders (PDF/TXT), pipeline (index/retrieve/generate)
│   ├── app.py                # Streamlit web UI
│   ├── run.py                # command-line chatbot
│   ├── evaluate.py           # runs test questions across models -> results/
│   ├── run_txt_baseline.py   # original sample code (for comparison)
│   ├── tests/test_questions.json
│   ├── results/              # evaluation outputs
│   ├── data/cs_handbook/     # CS_MajorHandbook.pdf (Task 2 knowledge base)
│   └── data/task1_demo/      # any PDF used to demo Task 1
├── docker/                   # Dockerfile + compose files
├── report/                   # final report
└── demo_video/               # demo videos (links if hosted externally)
```

## 1. Run locally (without Docker)

### Prerequisites
- [Ollama](https://ollama.com/download)
- Python 3.10–3.12 (python.org or Miniconda)

> **Windows tip:** models are stored in `C:\Users\<you>\.ollama` by default. To keep them on
> another drive, set the user environment variable `OLLAMA_MODELS=D:\ollama\models` and restart Ollama.

### Steps
```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:3b          # also try qwen2.5:0.5b / qwen2.5:1.5b / qwen2.5:7b

cd source_code
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Command line
```bash
python run.py -q "What are the core courses for the CS major?"
python run.py --interactive                                     # chat with history
python run.py --data-dir data/task1_demo -q "What is Task 3 about?"   # Task 1: any PDF
python run.py -q "..." --show-context                           # print retrieved chunks
python run.py --rebuild                                         # force re-indexing
```

### Web UI
```bash
streamlit run app.py      # opens http://localhost:8501
```

### Evaluation (Task 2)
```bash
python evaluate.py --models qwen2.5:0.5b qwen2.5:1.5b qwen2.5:3b
python evaluate.py --prompt-mode open --tag baseline-prompt
python evaluate.py --chunk-size 500 --chunk-overlap 100 --tag small-chunks
```
Results are written to `source_code/results/` as CSV (with a `verdict` column to grade by hand)
and Markdown.

## 2. Run with Docker (Task 3)

Requires [Docker Desktop](https://docs.docker.com/desktop/). Run every command from the **repository root**.

**Option A: full stack (Ollama in a container, models pulled automatically)**
```bash
docker compose -f docker/docker-compose.yml up --build
```
With an NVIDIA GPU:
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.gpu.yml up --build
```

**Option B: app container only, reusing the Ollama on your host**
```bash
docker compose -f docker/docker-compose.host-ollama.yml up --build
```

Open <http://localhost:8501>. The first start downloads models (~2.3 GB) and embeds the handbook.

| Item | Details |
|---|---|
| Documents | `source_code/data` is mounted read-only at `/app/data`, so you can swap PDFs without rebuilding |
| Vector store | named volume `vector_store` at `/app/vector_store` (persists across restarts) |
| Models | named volume `ollama_models` |
| Change the LLM | `RAG_LLM_MODEL=qwen2.5:1.5b docker compose -f docker/docker-compose.yml up` (PowerShell: `$env:RAG_LLM_MODEL="qwen2.5:1.5b"`) |
| Stop / clean | `docker compose -f docker/docker-compose.yml down` (add `-v` to delete volumes) |

Plain `docker` without Compose:
```bash
docker build -f docker/Dockerfile -t rag-handbook .
docker run -p 8501:8501 -e OLLAMA_URL=http://host.docker.internal:11434 \
  -v "$(pwd)/source_code/data:/app/data:ro" rag-handbook
```

## Configuration

All settings live in [`source_code/rag/config.py`](source_code/rag/config.py) and can be overridden with environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama server |
| `RAG_LLM_MODEL` | `qwen2.5:3b` | generation model |
| `RAG_EMBED_MODEL` | `nomic-embed-text` | embedding model |
| `RAG_DATA_DIR` | `data/cs_handbook` | folder of PDFs/TXTs |
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | `1000` / `200` | characters |
| `RAG_TOP_K` | `5` | retrieved chunks |
| `RAG_TEMPERATURE` | `0.1` | sampling temperature |
| `RAG_NUM_CTX` | `8192` | LLM context window (Ollama's default is too small for 5 chunks) |
| `RAG_MAX_TOKENS` | `1024` | answer length cap (stops small-model repetition loops) |
| `RAG_REWRITE_FOLLOWUPS` | `1` | rewrite follow-up questions into standalone ones before retrieval |
| `RAG_PROMPT_MODE` | `strict` | `strict` = documents only, `open` = baseline (falls back to model knowledge) |
| `RAG_TASK_PREFIXES` | `1` | add `search_document:`/`search_query:` prefixes for nomic |

## Improvements over the baseline sample

1. **PDF loading per page** with page metadata, so answers cite `(p. N)` and the UI shows the source page.
2. **Index fingerprinting**: the baseline reused any existing `vector_store/` even after you changed the
   chunk size or the documents. Here the index folder name is a hash of the files and indexing settings.
3. **Cosine similarity** (`hnsw:space=cosine`) instead of an ad-hoc `1/(1+L2)` score.
4. **nomic-embed-text task prefixes**, which the model was trained with.
5. **Larger context window** (`num_ctx=8192`), so retrieved chunks aren't silently truncated.
6. **Grounded "strict" prompt** that refuses rather than hallucinating, with the baseline prompt kept for comparison.
7. **Lower temperature** (0.1 vs 0.7) for factual Q&A.

8. **Follow-up rewriting**: "which courses help with the second one?" is rewritten to a standalone question before retrieval.
9. **Answer length cap** (`num_predict=1024`): without it, qwen2.5:0.5b fell into repetition loops (one answer exceeded 390,000 characters).

## Known limitations
- Text inside images or scanned pages is not extracted (no OCR). Page 10 of the CS handbook (the student-journey diagram) is an image.
- Tables (e.g. the PLO-course alignment table) are flattened into plain text by pypdf, so the model can't tell which column a mark belongs to.
- Small models (0.5b) often ignore instructions, mix up course codes, or answer out-of-scope questions anyway.

## Demo videos
See [`demo_video/`](demo_video/).
