# Report outline (target 1,800–2,200 words, export to PDF)

> This is a working outline. The draft gets written once real evaluation results are in
> `source_code/results/`, because the evaluation and lessons-learned sections must describe what
> actually happened. Rewrite the final version in your own words.

1. **Introduction** (~150 words): LLM limitations (outdated knowledge, hallucination, no access to private documents), why RAG, and why local RAG (privacy, cost, offline use).
2. **System architecture** (~350 words): diagram plus each component and the chosen tool. Loader (pypdf, per page) → splitter (recursive, 1000/200) → nomic-embed-text with task prefixes → Chroma (cosine) → top-k → strict prompt → qwen2.5 via Ollama → Streamlit/CLI.
3. **Task 1: PDF support** (~150 words): page-level extraction, cleaning, page metadata, OCR limitation (FAQ 5).
4. **Task 2: Handbook chatbot and evaluation** (~600 words)
   - Test set: 16 questions across 6 categories (requirements, courses, outcomes, policies, multi-hop, out-of-scope).
   - Results table per model: correct / incomplete / incorrect / ambiguous counts and average latency.
   - 2 correct examples, plus 1 each of incomplete, incorrect and ambiguous, with the reason (retrieval miss vs. generation error, table flattening, chunk boundary, small model ignoring instructions).
   - Ablations: strict vs. open prompt; with vs. without nomic prefixes; chunk size 500 vs. 1000; top-k 3 vs. 5 vs. 8.
5. **Task 3: Docker deployment** (~250 words): image design, Compose services, volumes, env config, GPU override, host-Ollama alternative, problems hit.
6. **Task 4: User interface** (~200 words): design choices (streaming, sources, controls, history), screenshots.
7. **Lessons learned** (~200 words), e.g. the stale index bug in the baseline, Ollama's default context window, and how much model size matters.
8. **Limitations and future work** (~150 words): OCR, table-aware parsing, hybrid BM25 + vector search, reranker, query rewriting for follow-ups, RAGAS-style automatic evaluation.
9. **References**
