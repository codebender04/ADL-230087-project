# Graded answers - qwen2.5:3b (main configuration)

Source run: `eval_20261114-174521-models` · embed=nomic-embed-text, chunk=1000/200, top_k=5, strict prompt, temperature 0.1.

Each answer was checked against the handbook text. **Failure cause** says where it went wrong: *retrieval* = the needed chunk was not among the 5 retrieved; *generation* = the information was retrieved but the model left it out or misread it; *document* = the handbook itself is inconsistent.

## Summary

| Verdict | Count |
|---|---|
| correct | 10 |
| incomplete | 4 |
| incorrect | 3 |
| ambiguous | 1 |
| **total** | **18** |

| Failure cause | Questions |
|---|---|
| Retrieval / chunk boundaries | Q08, Q14, (Q05 partly) |
| Generation (omission, misreading) | Q02, Q09, Q12, (Q05 partly) |
| Multi-hop reasoning | Q13 |
| Inconsistent document | Q15 |

Note: the page-level *retrieval hit* metric in the evaluation files is 100%, but Q08 and Q14 show that the right **page** can be retrieved while the chunk holding the answer is not.

## Answers

| ID | Question | Verdict | Cause | Why |
|---|---|---|---|---|
| Q01 | How many credits are required for the Computer Science major? | **correct** | - | 56 credits, matches p.7. |
| Q02 | What courses are required for the Computer Science major? | **incomplete** | generation | Lists 7 of the 8 requirements: leaves out 'Capstone I & II (8 credits) or two extra intermediate/advanced courses'. Its own list adds up to 48 credits but it still says 56. The capstone line WAS in the 4th retrieved chunk, so the model had it and dropped it. |
| Q03 | What are the requirements for a minor in Computer Science? | **correct** | - | All six minor courses and the 24-credit total, matches p.7. |
| Q04 | Who is eligible to take the Capstone project? | **correct** | - | Major GPA of 3.5 and an approved application, cites p.9. |
| Q05 | What advanced courses can CS students choose from? | **incomplete** | generation + chunking | Lists 13 of 15 advanced courses. 'Computational Social Media' was in the retrieved p.8 chunk but omitted (generation). 'Bioinformatics' continues onto p.9 and that chunk was not retrieved (page/chunk boundary). |
| Q06 | What are the prerequisites for Data Structures & Algorithms? | **correct** | - | CS101, matches the catalogue (p.13) and description (p.14). |
| Q07 | What programming language is mainly used in CS201? | **correct** | - | Java, cites p.14 (doesn't mention the secondary Python/C++, but the question asked for the main language). |
| Q08 | How often is Computer Networks offered? | **incorrect** | retrieval | Says 'once a semester (p.16)'; the catalogue (p.13) says 'On holding'. The chunk with the CS210 catalogue row was not retrieved - only neighbouring table rows and the p.16 course description (which has no schedule). The model guessed and cited the wrong page. |
| Q09 | What are the major learning outcomes of the CS program? | **incorrect** | generation (table flattening) | Asked for the Major LOs but listed the Core LOs (CoreLO 1-4). Both tables sit together on p.5 and PDF extraction flattens them into plain text, so the model confused the two. |
| Q10 | What careers have CS graduates gone into? | **correct** | - | All seven careers from p.5. |
| Q11 | When can a student formally declare Computer Science as their major? | **correct** | - | At least two CS courses, MATH 202 counts, cites p.7. |
| Q12 | Can exploratory courses count toward the CS major? | **incomplete** | generation | 'Yes' is right, but it misses the limit (only up to 2 exploratory courses / 8 credits count) and wrongly says exploratory courses are 'required for the major'. The correct sentence was in the retrieved p.7 chunk. |
| Q13 | If I want to take Advanced Deep Learning, which courses must I complete first? | **incomplete** | multi-hop reasoning | Gives only the direct prerequisite CS313. The full chain is CS311 <- CS313 <- CS208 <- CS103; following it needs several catalogue rows combined, and the model stops after one hop. |
| Q14 | What is the difference between graduating with and without honors in CS? | **incorrect** | retrieval (chunk boundary) | Says it couldn't find it, but p.8 explains it. The sentence is split across two chunks: only '...to graduate without honors' was retrieved, not '...do the capstone to graduate with honors'. Given what it saw, declining was reasonable - the failure is in chunking. |
| Q15 | What degree is awarded after completing the CS program? | **ambiguous** | document | Answers 'B.S. in Computer Science', matching p.1 - but p.6 says 'Bachelor of Science in Applied Mathematics' (a copy-paste error in the handbook). p.6 was retrieved; the model silently picked one version without flagging the contradiction. |
| Q16 | What is the tuition fee for the CS program? | **correct** | - | Correctly says the handbook doesn't cover tuition. |
| Q17 | Can I transfer credits from another university toward the CS major? | **correct** | - | Correctly says the handbook doesn't cover transfer credits (1.5b and the uncapped 0.5b invented a policy here). |
| Q18 | Who won the 2022 FIFA World Cup? | **correct** | - | Correctly declines an unrelated question. |
