# Evaluation summary

All runs used the same 18 test questions (`tests/test_questions.json`): 15 that the handbook
answers and 3 that are out of scope (tuition, transfer credits, World Cup).
Default setup: nomic-embed-text, 1000-character chunks with 200 overlap, top-5 retrieval,
strict prompt, temperature 0.1. Full answers are in the `eval_*.md` / `eval_*.csv` files.

**How to read the columns**
- **Keyword recall:** the share of expected key terms that appear in the answer. Higher is better; it's a rough automatic check.
- **Retrieval hit:** a correct *page* was among the 5 retrieved chunks. It only checks the page, not the exact chunk, so it can miss chunk-level failures.
- **Out-of-scope declined:** the model said "not in the documents" for an out-of-scope question. Higher is better.
- **In-scope wrongly declined:** the model said "not in the documents" for a question the handbook *does* answer. Lower is better.

## 1. Model size comparison (`eval_20261114-174521-models`)

| Model | Parameters | Keyword recall | Retrieval hit | Out-of-scope declined | In-scope wrongly declined | Avg. generation time |
|---|---|---|---|---|---|---|
| qwen2.5:0.5b | 0.5 B | 0.60 | 1.00 | 3/3 | 0/15 | 0.4 s |
| qwen2.5:1.5b | 1.5 B | 0.67 | 1.00 | **2/3** (invented a transfer-credit policy) | 0/15 | 0.5 s |
| **qwen2.5:3b** | 3 B | **0.68** | 1.00 | **3/3** | 1/15 (Q14) | 1.0 s |

Retrieval is identical for all three models, because the same embedding model and index are used.
The differences come only from the model that writes the answer.

## 2. Other experiments (qwen2.5:3b)

| Experiment | Change | Keyword recall | Out-of-scope declined | In-scope wrongly declined | Result |
|---|---|---|---|---|---|
| Main setup | - | 0.68 | 3/3 | 1/15 | baseline for comparison |
| Open prompt (`open-prompt`) | sample code's prompt, which may use the model's own knowledge | 0.77 | 3/3 | 0/15 | longer answers that hit more keywords, but it got Q14 (honors) backwards |
| No nomic prefixes (`no-prefixes`) | no `search_query:` / `search_document:` | 0.66 | 3/3 | 2/15 | slightly worse retrieval, so more wrong "not found" answers |
| 500-character chunks (`chunk500`) | chunk 500 / overlap 100 | 0.67 | 3/3 | 3/15 | small chunks split facts more often, giving the most wrong "not found" answers |
| No length cap (`models-uncapped`) | no `num_predict` limit | 0.62 (0.5b) | 2/3 (0.5b) | - | 0.5b fell into repetition loops: 41 s average, and one answer was over 390,000 characters |

## 3. Hand-graded answers, qwen2.5:3b (`verdicts_qwen2.5-3b.md`)

| Correct | Incomplete | Incorrect | Ambiguous |
|---|---|---|---|
| 10 | 4 | 3 | 1 |

| Failure cause | Questions |
|---|---|
| Retrieval / chunk boundaries | Q08, Q14 (Q05 partly) |
| Generation (left out or misread retrieved information) | Q02, Q09, Q12 (Q05 partly) |
| Multi-hop reasoning | Q13 |
| Handbook contradicts itself | Q15 |
