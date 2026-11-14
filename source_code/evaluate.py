#!/usr/bin/env python3
"""Run the Task 2 test questions against one or more models and save the results.

Examples:
  python evaluate.py                                   # default model
  python evaluate.py --models qwen2.5:0.5b qwen2.5:1.5b qwen2.5:3b
  python evaluate.py --prompt-mode open                # baseline prompt, for comparison
  python evaluate.py --chunk-size 500 --chunk-overlap 100

Output (in results/):
  eval_<timestamp>.csv  - one row per (model, question), with a blank 'verdict' column
                          for you to fill in: correct / incomplete / incorrect / ambiguous
  eval_<timestamp>.md   - the same results, readable, to paste into the report
Automatic metrics (only when expected_* fields are filled in test_questions.json):
  keyword_recall   - share of expected keywords that appear in the answer
  retrieval_hit    - 1 if any retrieved chunk comes from an expected page
"""

import argparse
import csv
import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from rag import RAGPipeline, Settings

HERE = Path(__file__).resolve().parent


def _norm(text: str) -> str:
    # "CS 101", "CS-101" and "cs101" should all match
    return "".join(ch for ch in text.lower() if ch.isalnum() or ch == ".")


def keyword_recall(answer: str, keywords):
    if not keywords:
        return ""
    a = _norm(answer)
    return round(sum(_norm(k) in a for k in keywords) / len(keywords), 2)


REFUSAL = "couldn't find"


def retrieval_hit(sources, pages):
    if not pages:
        return ""
    return int(any(s.page in pages for s in sources))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", default=None)
    p.add_argument("--questions", default=str(HERE / "tests" / "test_questions.json"))
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--chunk-size", type=int, default=None)
    p.add_argument("--chunk-overlap", type=int, default=None)
    p.add_argument("--prompt-mode", choices=["strict", "open"], default=None)
    p.add_argument("--no-prefixes", action="store_true", help="Disable nomic task prefixes")
    p.add_argument("--tag", default="", help="Label added to the output filename")
    args = p.parse_args()

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
                "refused": REFUSAL in ans.answer.lower(),
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

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig opens cleanly in Excel
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Evaluation {stamp}\n\n`{config}`\n\n")
        for model in models:
            mr = [r for r in rows if r["model"] == model]
            avg_t = sum(r["gen_seconds"] for r in mr) / len(mr)
            kw = [r["keyword_recall"] for r in mr if r["keyword_recall"] != ""]
            hits = [r["retrieval_hit"] for r in mr if r["retrieval_hit"] != ""]
            oos = [r for r in mr if r["category"] == "out of scope"]
            f.write(f"## {model}\n\n"
                    f"| avg keyword recall | retrieval hit rate | out-of-scope refused | avg generation |\n"
                    f"|---|---|---|---|\n"
                    f"| {sum(kw)/max(len(kw),1):.2f} | {sum(hits)/max(len(hits),1):.2f} | "
                    f"{sum(r['refused'] for r in oos)}/{len(oos)} | {avg_t:.1f}s |\n\n")
            for r in mr:
                f.write(f"### {r['id']} [{r['category']}] {r['question']}\n\n"
                        f"**Expected:** {r['expected']}\n\n**Answer:** {r['answer']}\n\n"
                        f"*Retrieved:* {r['retrieved']} · keyword recall {r['keyword_recall']} · "
                        f"retrieval hit {r['retrieval_hit']}\n\n")
    print(f"\nSaved {csv_path}\nSaved {md_path}")


if __name__ == "__main__":
    main()
