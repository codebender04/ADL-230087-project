# Demo videos

Put the four recordings here (or links, if they are too large for Canvas).

| Video | File / link |
|---|---|
| Task 1 – PDF support | |
| Task 2 – Handbook chatbot | |
| Task 3 – Docker deployment | |
| Task 4 – Web UI | |

## Suggested shot lists

**Task 1 – PDF support (~2–3 min)**
1. Show `rag/loaders.py`: `load_pdf` extracts text page by page and keeps page numbers. Compare it with the baseline's `.txt`-only loader.
2. Run `python run.py --data-dir data/task1_demo --rebuild -q "..."` and point out the "Loaded PDF … pages" and "Embedding N chunks" logs.
3. Ask a question whose answer is only in that PDF, and show the answer with its `p. N` source.

**Task 2 – Handbook chatbot (~4–5 min)**
1. Briefly explain the pipeline (`rag/pipeline.py`): retrieve → strict prompt → generate.
2. Live: 2 correct answers, then 1 incomplete/incorrect answer, and explain *why* (open the retrieved chunks with `--show-context`).
3. Show an out-of-scope question being refused.
4. Show `evaluate.py` output and the model comparison table.

**Task 3 – Docker (~3 min)**
1. Walk through the `Dockerfile` and `docker-compose.yml` (services, volumes, env vars).
2. `docker compose -f docker/docker-compose.yml up --build`, then show `docker ps`.
3. Open http://localhost:8501 and ask one question.
4. Restart the stack to show that the index persists (no re-embedding).

**Task 4 – Web UI (~2–3 min)**
1. Ask an example question and show the streamed answer and the Sources expander.
2. Ask a follow-up to show conversation history, then try changing the model or top-k.
3. Clear and export the chat.
