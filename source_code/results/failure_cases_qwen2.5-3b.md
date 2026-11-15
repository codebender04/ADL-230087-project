# Failure cases – qwen2.5:3b

The 8 questions the main model (qwen2.5:3b, strict prompt) did not answer fully correctly.
Each one shows the question, what the model answered, what the handbook actually says, and why it failed.
The answers are copied from the evaluation run `eval_20261114-174521-models`. Running them again
with `python run.py -q "..."` gives the same answers, because the temperature is low (0.1).

**Failure types**
- **Retrieval / chunking:** the chunk holding the answer was not among the 5 chunks given to the model.
- **Generation:** the right chunk *was* given to the model, but it left the information out or misread it.
- **Multi-hop:** the answer needs several facts chained together, and the model stopped after one step.
- **Document:** the handbook itself is inconsistent.

Overview:

| ID | Question | Verdict | Failure type |
|---|---|---|---|
| Q14 | Difference between graduating with and without honors | incorrect | retrieval (chunk boundary) |
| Q08 | How often is Computer Networks offered? | incorrect | retrieval |
| Q09 | Major learning outcomes | incorrect | generation (flattened table) |
| Q02 | Courses required for the major | incomplete | generation |
| Q12 | Do exploratory courses count? | incomplete | generation |
| Q05 | Advanced courses to choose from | incomplete | generation + chunking |
| Q13 | Courses needed before Advanced Deep Learning | incomplete | multi-hop reasoning |
| Q15 | Degree awarded | ambiguous | document contradiction |

---

## Q14 – incorrect (retrieval / chunk boundary)
**Question:** What is the difference between graduating with and without honors in CS?

**qwen2.5:3b answered:**
> I couldn't find that in the documents.

**The handbook says (p. 8):** students who complete Capstone I & II graduate **with honors**. Students who take two
extra intermediate/advanced courses instead graduate **without honors**.

**Why it failed:** that sentence was cut in half when the text was split into 1,000-character chunks.
Only the second half ("...to graduate without honors") was retrieved. With half the information,
the model correctly refused to guess. The problem is in **chunking**, not in the model. Run it with `--show-context` to see this.

---

## Q08 – incorrect (retrieval)
**Question:** How often is Computer Networks offered?

**qwen2.5:3b answered:**
> Computer Networks is offered once a semester (p.16).

**The handbook says (p. 13, course catalogue):** CS210 Computer Networks is **"On holding"**, so it is not currently scheduled.

**Why it failed:** the catalogue chunk containing the CS210 row was not retrieved. Only neighbouring table rows
and the course description on p. 16 (which says nothing about scheduling) were. The model then **guessed**
and attached a real page number to the guess, which makes the wrong answer look trustworthy.

---

## Q09 – incorrect (generation, flattened table)
**Question:** What are the major learning outcomes of the CS program?

**qwen2.5:3b answered (shortened):**
> The Major Learning Outcomes ... Here are the Core Learning Outcomes (Core LOs):
> CoreLO 1 ... global awareness ... CoreLO 2 ... CoreLO 3 ... CoreLO 4 ...

**The handbook says (p. 5):** MLO1 fundamentals in theory and systems; MLO2 explain emerging areas (AI, ML, data science);
MLO3 develop real-world applications.

**Why it failed:** p. 5 has two tables next to each other, Core LOs and Major LOs. pypdf turns tables into
plain lines of text, so the boundary between them is lost. The model even says "Major LOs" and then
lists the **Core** LOs.

---

## Q02 – incomplete (generation)
**Question:** What courses are required for the Computer Science major?

**qwen2.5:3b answered:**
> CS 101 (4) · CS 201 (4) · CS 203 (4) · MATH 202 (4) · Three intermediate courses (12) · CS 302 (4) · Four advanced courses (16)
> Total required credits for the major are 56.

**The handbook says (p. 7–8):** the same list **plus Capstone I & II (8 credits)**, or two extra intermediate/advanced courses.

**Why it failed:** the capstone line *was* in a retrieved chunk, but the model dropped it. Its own list adds up to
**48** credits, yet it states 56. It copied the total without checking it.

---

## Q12 – incomplete (generation)
**Question:** Can exploratory courses count toward the CS major?

**qwen2.5:3b answered:**
> Yes, exploratory courses can count toward the CS major. ... exploratory courses (2 courses ...) are required for the major and can count towards the total of 56 credits. (p.7)

**The handbook says (p. 7):** yes, but only **up to 2 exploratory courses (8 credits)** can count.

**Why it failed:** "Yes" is right, but it leaves out the limit and wrongly says exploratory courses are "required for the major".
The correct sentence was in the retrieved chunk.

---

## Q05 – incomplete (generation + chunking)
**Question:** What advanced courses can CS students choose from?

**qwen2.5:3b answered:** 13 courses (Foundations of Software Engineering ... Optimization).

**The handbook lists (p. 8–9):** 15 courses. Missing: **Computational Social Media** and **Bioinformatics**.

**Why it failed:** Computational Social Media was in a retrieved chunk but left out (generation). Bioinformatics is on
the next page, in a chunk that was not retrieved (chunking).

---

## Q13 – incomplete (multi-hop reasoning)
**Question:** If I want to take Advanced Deep Learning, which courses must I complete first?

**qwen2.5:3b answered:**
> To take the course Advanced Deep Learning (CS311), you must complete the prerequisite course Deep Learning for Artificial Intelligence (CS313) first.

**The handbook says (course descriptions):** CS311 needs CS313, which needs CS208, which needs CS103.

**Why it failed:** the direct prerequisite is correct, but the full answer needs three catalogue rows chained together.
The model stops after the first step. Each step also needs its own search, but RAG only searches once, using the original question.

---

## Q15 – ambiguous (document contradiction)
**Question:** What degree is awarded after completing the CS program?

**qwen2.5:3b answered:**
> The degree awarded after completing the CS program is a Bachelor of Science (B.S.) in Computer Science.

**The handbook says:** "Computer Science" on p. 1, but **"Bachelor of Science in Applied Mathematics"** on p. 6,
which looks like a copy-paste error in the handbook.

**Why it's ambiguous:** the answer is most likely right, but p. 6 was retrieved too, and the model picked one version
without mentioning the contradiction. A careful assistant should flag it.
