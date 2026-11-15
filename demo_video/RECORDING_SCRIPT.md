# Recording script for the four demo videos

Keep this file open on a second screen or on your phone while you record.
**Do** = what to do on screen. **Say** = a suggested line, in your own words.
Aim for 2–4 minutes per video. Practise once before recording, because live answers
can differ slightly from the evaluation run.

## Before every recording

1. Ollama is running (its icon is in the system tray). For Video 3 it does not need to be.
2. Open PowerShell in the project folder:
   ```powershell
   cd "D:\Courses\AY 26-27\Advanced Deep Learning\Final Project\ADL-project\source_code"
   .venv\Scripts\activate
   ```
3. Make the terminal font bigger (Ctrl + mouse wheel) so the text is readable in the video.
4. Use any screen recorder: Windows **Snipping Tool → Record** (Win+Shift+R), the Xbox Game Bar (Win+G), or OBS.
5. Ask one warm-up question before you start recording, so the model is already loaded and the answers come quickly.

---

## Video 1 – Task 1: PDF support (~2–3 min)

**Goal:** show that the system can now read PDFs, not only `.txt` files.

| # | Do | Say |
|---|---|---|
| 1 | Open `run_txt_baseline.py` and scroll to `load_text_files`. | "The sample code only loads `.txt` files, so it can't read a PDF at all." |
| 2 | Open `rag/loaders.py` and show `load_pdf`. | "I added a PDF loader with pypdf. It reads the PDF **page by page** and saves the file name and page number with each page. That lets the chatbot say which page an answer came from. It also cleans the text and warns me about pages with no text, like a scanned image, which would need OCR." |
| 3 | Run:<br>`python run.py --data-dir data/task1_demo --rebuild -q "What should the submission folder be named?"` | "To test it, I'm pointing the chatbot at a different PDF, the project assignment itself." |
| 4 | Point at the log lines `Loaded PDF: Final-project-ADL.pdf (N pages with text)` and `Embedding N chunks`. | "It loaded every page, split the text into chunks of about 1,000 characters, and turned each chunk into a vector with the embedding model." |
| 5 | Point at the answer and the **Sources** list under it. | "The answer `ADL-<StudentID>-project` is correct, and the Sources list shows it came from page 11 of the PDF." |
| 6 | *(optional)* Ask one more:<br>`python run.py --data-dir data/task1_demo -q "How much is the Docker task worth?"` | "This time there's no re-indexing. The saved index is reused, so it starts much faster. The answer is 20%." |

---

## Video 2 – Task 2: Handbook chatbot and evaluation (~4–5 min)

**Goal:** show that the chatbot answers handbook questions, and that you tested and understand
when it is right and when it is wrong.

| # | Do | Say |
|---|---|---|
| 1 | Show the README diagram (or `rag/pipeline.py`). | "This is how it works. The handbook PDF is split into chunks and embedded with nomic-embed-text, and the vectors are stored in Chroma. For each question, I find the 5 most similar chunks, put them into a prompt, and qwen2.5:3b writes the answer. The prompt tells the model to answer **only** from those chunks, to cite pages, and to say *I couldn't find that* otherwise." |
| 2 | `python run.py -q "How many credits are required for the Computer Science major?"` | "Correct: 56 credits, page 7." |
| 3 | `python run.py -q "Who is eligible to take the Capstone project?"` | "Also correct: a major GPA of 3.5 and an approved application." |
| 4 | `python run.py -q "What is the difference between graduating with and without honors in CS?" --show-context` | "This is a failure. The handbook *does* explain this on page 8, but the model says it couldn't find it." |
| 5 | Scroll through the printed chunks. | "Here's why. The answer sentence was cut in half when the text was split into chunks. Only the half about graduating *without* honors was retrieved. So this is a **retrieval and chunking** problem, not the model making something up. Given what it saw, saying it couldn't find the answer was reasonable." |
| 6 | `python run.py -q "Who won the 2022 FIFA World Cup?"` | "An out-of-scope question. It correctly says it's not in the documents instead of using its own knowledge." |
| 7 | Open `tests/test_questions.json` and scroll briefly. | "To test it properly, I wrote 18 questions: program requirements, courses, learning outcomes, policies, multi-step questions, an ambiguous one, and three that are out of scope." |
| 8 | Open `results/SUMMARY.md` and show table 1 (model size comparison). | "`evaluate.py` runs all 18 questions on three model sizes: 0.5, 1.5 and 3 billion parameters. The 3b model followed the rules best. The 1.5b model invented a transfer-credit policy, and 0.5b often ignored the instructions." |
| 9 | Scroll to table 3 in `SUMMARY.md` (or open `results/verdicts_qwen2.5-3b.md` for the details). | "I graded the 3b answers by hand: 10 correct, 4 incomplete, 3 incorrect and 1 ambiguous. Most errors come from chunking, for example a split sentence or a flattened table, or from the small model leaving out information it was given. The ambiguous one is because the handbook contradicts itself: page 6 says 'Applied Mathematics' instead of 'Computer Science'." |

---

## Video 3 – Task 3: Docker deployment (~3–4 min)

**Goal:** show that anyone can run the whole system with one command, without installing Python or Ollama.

Before recording: open Docker Desktop and wait for "Engine running". **Quit the Ollama tray app**, which
shows that the container doesn't rely on your own Ollama. Then open PowerShell in the
**repository root** (`ADL-project`, not `source_code`).

| # | Do | Say |
|---|---|---|
| 1 | Open `docker/Dockerfile`. | "The Dockerfile is the recipe for the app image. It starts from Python 3.11, installs the requirements, copies the code, runs as a non-root user and starts Streamlit on port 8501." |
| 2 | Open `docker/docker-compose.yml`. | "Compose runs three containers together. **ollama** is the model server. **model-init** downloads the two models once and then exits. **app** is my chatbot. The handbook folder is mounted, so documents can be swapped without rebuilding. The models and the vector index are kept in named volumes, so they survive restarts." |
| 3 | Run:<br>`docker compose -f docker/docker-compose.yml -f docker/docker-compose.gpu.yml up --build -d` | "This builds the image and starts everything. The second file gives the Ollama container my GPU." |
| 4 | `docker ps` | "The ollama and app containers are running. model-init has already finished." |
| 5 | `docker compose -f docker/docker-compose.yml logs app` | "The app embedded the handbook inside the container." |
| 6 | Open http://localhost:8501 and ask a question. | "The same chatbot, now running entirely inside Docker." |
| 7 | `docker compose -f docker/docker-compose.yml restart app`, then show the logs again. | "After a restart it says *Loaded existing index* instead of embedding again. The vector store volume kept the index." |
| 8 | `docker compose -f docker/docker-compose.yml down` | "This stops it. Adding `-v` would also delete the volumes." |

Tip: if the first `up` has to download models (~2.3 GB), pause the recording or cut that part out.
When you're done, start the Ollama tray app again.

---

## Video 4 – Task 4: Web interface (~2–3 min)

**Goal:** show that a non-technical user can use the chatbot in a browser.

Run `streamlit run app.py` from `source_code` (or use the Docker version from Video 3).

| # | Do | Say |
|---|---|---|
| 1 | Show the page. | "This is the web interface, built with Streamlit. There's a chat box, example questions, and settings in the sidebar." |
| 2 | Click an example question. | "The answer streams in word by word, and below it I can see the model used and how long retrieval and generation took." |
| 3 | Open the **Sources** expander. | "These are the exact chunks and pages the answer was based on, so the user can check it against the handbook." |
| 4 | Ask: *"What advanced courses can CS students choose from?"* then the follow-up *"Which of those are about AI?"* | "The interface remembers the conversation. Before searching, the follow-up is rewritten into a full question, shown under 'searched as'. Without that, 'those' wouldn't match anything in the handbook." |
| 5 | In the sidebar, change the model to qwen2.5:0.5b and ask the same question again. | "I can switch models, chunk count and temperature without restarting. The smaller model is faster but less accurate." |
| 6 | Turn off **Answer only from the handbook** and ask *"What is the tuition fee?"* | "With strict mode off, it behaves like the original sample code. It may answer from its own knowledge, which is risky for a handbook assistant." |
| 7 | Click **Export**, then **Clear chat**. | "I can download the conversation as a Markdown file and clear the chat." |

---

## After recording

- Save the files as `task1_pdf.mp4`, `task2_chatbot.mp4`, `task3_docker.mp4` and `task4_webui.mp4` in this folder.
- If they're too large for Canvas, upload them to Google Drive or OneDrive, set the links to "anyone with the link can view", and fill in the table in `README.md` and in the report.
- Take 2–3 screenshots of the web interface during Video 4. The report needs them.
