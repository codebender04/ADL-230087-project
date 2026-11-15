#!/usr/bin/env python3
"""Run the Task 2 test questions against one or more models and save the results.

Examples:
  python evaluate.py                                   # default model
  python evaluate.py --models qwen2.5:0.5b qwen2.5:1.5b qwen2.5:3b
  python evaluate.py --prompt-mode open                # baseline prompt, for comparison
  python evaluate.py --chunk-size 500 --chunk-overlap 100
  python evaluate.py --recompute results/eval_*.csv    # re-score saved answers (no model calls)

Output (in results/):
  eval_<date>-<time>-<tag>.csv - one row per (model, question), with a blank 'verdict' column
                                 for you to fill in: correct / incomplete / incorrect / ambiguous
  eval_<date>-<time>-<tag>.md  - the same results, readable, with a summary table per model

Automatic metrics (rough indicators only - the 'verdict' column is the real judgement):
  keyword_recall    - share of expected keywords that appear in the answer
  retrieval_hit     - 1 if any retrieved chunk comes from an expected page
  says_not_in_docs  - the answer states the documents don't contain the information
                      (good for out-of-scope questions, bad for in-scope ones)
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUESTIONS = HERE / "tests" / "test_questions.json"
OUT_OF_SCOPE = "out of scope"

# Phrasings meaning "the documents don't have this". The strict prompt asks for
# "I couldn't find that in the documents", but the baseline prompt lets the model word it
# freely ("The context provided does not contain any information about ...").
NOT_IN_DOCS = re.compile(
    r"could(?:n't|n’t| not) find"
    r"|(?:does|do)(?:n't|n’t| not) (?:contain|provide|mention|include|cover)"
    r"|no (?:specific |relevant )?information"
    r"|not (?:mentioned|provided|included|covered|found) in",
    re.IGNORECASE,
)

FIELDS = ["model", "id", "category", "question", "expected", "answer", "says_not_in_docs",
          "retrieved", "best_score", "low_confidence", "keyword_recall", "retrieval_hit",
          "gen_seconds", "verdict", "notes"]


def _norm(text: str) -> str:
    # "CS 101", "CS-101" and "cs101" should all match
    return "".join(ch for ch in text.lower() if ch.isalnum() or ch == ".")


def keyword_recall(answer: str, keywords):
    if not keywords:
        return ""
    a = _norm(answer)
    return round(sum(_norm(k) in a for k in keywords) / len(keywords), 2)


def says_not_in_docs(answer: str) -> bool:
    return bool(NOT_IN_DOCS.search(answer))


def retrieval_hit(sources, pages):
    if not pages:
        return ""
    return int(any(s.page in pages for s in sources))


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_outputs(rows, csv_path: Path, md_path: Path, title: str, config: str):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig opens cleanly in Excel
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    models = list(dict.fromkeys(r["model"] for r in rows))           # keep first-seen order
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Evaluation {title}\n\n`{config}`\n\n")
        f.write("Columns: **keyword recall** = share of expected key terms in the answer; "
                "**retrieval hit** = a correct page was among the retrieved chunks; "
                "**out-of-scope: said not in docs** = the model admitted the handbook doesn't cover "
                "an out-of-scope question (higher is better); **in-scope: said not in docs** = it "
                "wrongly claimed the handbook doesn't cover an answerable question (lower is better).\n\n")
        for model in models:
            mr = [r for r in rows if r["model"] == model]
            times = [t for t in (_num(r["gen_seconds"]) for r in mr) if t is not None]
            kw = [v for v in (_num(r["keyword_recall"]) for r in mr) if v is not None]
            hits = [v for v in (_num(r["retrieval_hit"]) for r in mr) if v is not None]
            oos = [r for r in mr if r["category"] == OUT_OF_SCOPE]
            ins = [r for r in mr if r["category"] != OUT_OF_SCOPE]
            f.write(f"## {model}\n\n"
                    "| avg keyword recall | retrieval hit rate | out-of-scope: said not in docs "
                    "| in-scope: said not in docs | avg generation |\n|---|---|---|---|---|\n"
                    f"| {sum(kw)/max(len(kw),1):.2f} | {sum(hits)/max(len(hits),1):.2f} "
                    f"| {sum(r['says_not_in_docs'] for r in oos)}/{len(oos)} "
                    f"| {sum(r['says_not_in_docs'] for r in ins)}/{len(ins)} "
                    f"| {sum(times)/max(len(times),1):.1f}s |\n\n")
            for r in mr:
                f.write(f"### {r['id']} [{r['category']}] {r['question']}\n\n"
                        f"**Expected:** {r['expected']}\n\n**Answer:** {r['answer']}\n\n"
                        f"*Retrieved:* {r['retrieved']} · keyword recall {r['keyword_recall']} · "
                        f"retrieval hit {r['retrieval_hit']} · said not in docs {r['says_not_in_docs']}\n\n")


def recompute(paths):
    """Re-score saved answers with the current metrics. No models are called."""
    csv.field_size_limit(2**31 - 1)   # runaway answers can exceed the 128 KB default; Windows needs a 32-bit value
    questions = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    for p in map(Path, paths):
        with open(p, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            q = questions.get(r["id"], {})
            r["expected"] = q.get("expected_answer", r.get("expected", ""))
            r["says_not_in_docs"] = says_not_in_docs(r["answer"])
            r["keyword_recall"] = keyword_recall(r["answer"], q.get("expected_keywords"))
            r.setdefault("verdict", "")
            r.setdefault("notes", "")
        md = p.with_suffix(".md")
        config = "config unknown"
        if md.exists():
            with open(md, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("`"):
                        config = line.strip().strip("`")
                        break
        try:
            write_outputs(rows, p, md, p.stem.removeprefix("eval_"), config)
            print(f"Recomputed {p.name}")
        except PermissionError:
            print(f"SKIPPED {p.name}: file is open in another program (close Excel and rerun)")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", default=None)
    p.add_argument("--questions", default=str(QUESTIONS))
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--chunk-size", type=int, default=None)
    p.add_argument("--chunk-overlap", type=int, default=None)
    p.add_argument("--prompt-mode", choices=["strict", "open"], default=None)
    p.add_argument("--no-prefixes", action="store_true", help="Disable nomic task prefixes")
    p.add_argument("--tag", default="", help="Label added to the output filename")
    p.add_argument("--recompute", nargs="+", metavar="CSV",
                   help="Re-score existing result CSVs instead of running the models")
    args = p.parse_args()

    if args.recompute:
        recompute(args.recompute)
        return

    from rag import RAGPipeline, Settings   # imported here so --recompute works without Ollama

    s = Settings()
    ov = {}
    if args.top_k: ov["top_k"] = args.top_k
    if args.chunk_size: ov["chunk_size"] = args.chunk_size
    if args.chunk_overlap is not None: ov["chunk_overlap"] = args.chunk_overlap
    if args.prompt_mode: ov["prompt_mode"] = args.prompt_mode
    if args.no_prefixes: ov["use_task_prefixes"] = False
    s = replace(s, **ov)
    models = args.models or [s.llm_model]

    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    rag = RAGPipeline(s)
    config = (f"embed={s.embed_model}, chunk={s.chunk_size}/{s.chunk_overlap}, top_k={s.top_k}, "
              f"prompt={s.prompt_mode}, prefixes={s.use_task_prefixes}, temp={s.temperature}")
    print("Config:", config)

    rows = []
    for model in models:
        print(f"\n=== {model} ===")
        for q in questions:
            ans = rag.ask(q["question"], model=model)
            row = {
                "model": model, "id": q["id"], "category": q["category"],
                "question": q["question"], "expected": q.get("expected_answer", ""),
                "answer": ans.answer,
                "says_not_in_docs": says_not_in_docs(ans.answer),
                "retrieved": "; ".join(f"{x.label} ({x.score})" for x in ans.sources),
                "best_score": max((x.score for x in ans.sources), default=0),
                "low_confidence": ans.low_confidence,
                "keyword_recall": keyword_recall(ans.answer, q.get("expected_keywords")),
                "retrieval_hit": retrieval_hit(ans.sources, q.get("expected_pages")),
                "gen_seconds": round(ans.generation_seconds, 2),
                "verdict": "", "notes": "",
            }
            rows.append(row)
            print(f"[{q['id']}] {q['question']}\n  -> {ans.answer[:200].replace(chr(10), ' ')}"
                  f"\n  ({row['retrieved'][:120]}..., {row['gen_seconds']}s)")

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{args.tag}" if args.tag else "")
    csv_path, md_path = out_dir / f"eval_{stamp}.csv", out_dir / f"eval_{stamp}.md"
    write_outputs(rows, csv_path, md_path, stamp, config)
    print(f"\nSaved {csv_path}\nSaved {md_path}")


if __name__ == "__main__":
    main()
