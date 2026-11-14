#!/usr/bin/env python3
"""Command-line RAG chatbot over a folder of PDF / TXT files.

Examples:
  python run.py                                         # CS handbook, default question
  python run.py -q "What are the CS core courses?"
  python run.py --data-dir data/task1_demo -q "How much is the Docker task worth?"
  python run.py --interactive                           # chat loop
  python run.py --rebuild                               # force re-indexing
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from rag import RAGPipeline, Settings

DEFAULT_QUESTION = "What courses are required for the Computer Science major?"


def print_answer(ans, show_sources: int = 3):
    print("\nA: " + ans.answer + "\n")
    if ans.low_confidence:
        print("(low retrieval confidence - the documents may not cover this question)")
    print("Sources:")
    for s in ans.sources[:show_sources]:
        print(f"   {s.label}  score={s.score}")
    print(f"[{ans.model} | retrieval {ans.retrieval_seconds:.2f}s | "
          f"generation {ans.generation_seconds:.2f}s]")


def main():
    if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(description="Local RAG Q&A over PDF/TXT files")
    p.add_argument("--question", "-q", default=None, help="Question to ask")
    p.add_argument("--data-dir", "-d", default=None, help="Folder with .pdf/.txt files")
    p.add_argument("--model", "-m", default=None, help="Ollama LLM, e.g. qwen2.5:3b")
    p.add_argument("--top-k", "-k", type=int, default=None)
    p.add_argument("--chunk-size", type=int, default=None)
    p.add_argument("--chunk-overlap", type=int, default=None)
    p.add_argument("--prompt-mode", choices=["strict", "open"], default=None)
    p.add_argument("--rebuild", action="store_true", help="Re-index documents")
    p.add_argument("--interactive", "-i", action="store_true", help="Chat loop")
    p.add_argument("--show-context", action="store_true", help="Print retrieved chunks")
    args = p.parse_args()

    s = Settings()
    overrides = {}
    if args.data_dir:
        overrides["data_dir"] = Path(args.data_dir).resolve()
    if args.model:
        overrides["llm_model"] = args.model
    if args.top_k:
        overrides["top_k"] = args.top_k
    if args.chunk_size:
        overrides["chunk_size"] = args.chunk_size
    if args.chunk_overlap is not None:
        overrides["chunk_overlap"] = args.chunk_overlap
    if args.prompt_mode:
        overrides["prompt_mode"] = args.prompt_mode
    s = replace(s, **overrides)

    print(f"Embedding model: {s.embed_model} | LLM: {s.llm_model} | Ollama: {s.ollama_url}")
    rag = RAGPipeline(s, rebuild=args.rebuild)

    def handle(question, history):
        print("Q: " + question)
        ans = rag.ask(question, history=history)
        if args.show_context:
            for src in ans.sources:
                print(f"\n----- {src.label} (score {src.score}) -----\n{src.content}")
        print_answer(ans)
        return ans

    if not args.interactive:
        handle(args.question or DEFAULT_QUESTION, None)
        return

    history = []
    print("Interactive mode - type 'exit' to quit, 'clear' to reset history.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit"):
            break
        if q.lower() == "clear":
            history = []
            continue
        if q:
            ans = handle(q, history)
            history += [{"role": "user", "content": q}, {"role": "assistant", "content": ans.answer}]


if __name__ == "__main__":
    main()
