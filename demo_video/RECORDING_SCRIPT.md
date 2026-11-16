# Recording script for the four demo videos

Keep this file open on a second screen or on your phone while you record.
**Do** = what to do on screen. **Say** = a suggested line, in your own words.
Aim for 2–4 minutes per video. Practise once before recording, because live answers
can differ slightly from the evaluation run.

## Before every recording

1. Ollama is running (its icon is in the system tray). For Video 3 it does not need to be.
2. Open PowerShell in the `source_code` folder (for Videos 1, 2 and 4; **Video 3 is different**, see its setup):
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

## Video 2 – Task 2: Handbook chatbot and evaluation (~5 min)

**Goal:** show that the chatbot answers handbook questions, and that you tested it and understand
**why** it is right or wrong. The "why" matters most.

Files to have open in tabs before recording (all in `source_code/`):
`rag/pipeline.py`, `tests/test_questions.json`, `results/SUMMARY.md`, `results/failure_cases_qwen2.5-3b.md`.
Open the `.md` files in VS Code's preview (Ctrl+Shift+V) so the tables look clean.

### Part A – How it works (~45 s)

| # | Do | Say |
|---|---|---|
| 1 | Show the diagram at the top of the README (or `rag/pipeline.py`). | "For Task 2, the knowledge base is the CS Major Handbook. The PDF is split into chunks of about 1,000 characters, and each chunk is turned into a vector with nomic-embed-text and stored in Chroma. When a question comes in, I find the 5 most similar chunks and put them in a prompt. qwen2.5:3b writes the answer. The prompt says: answer **only** from these chunks, cite the page, and if the answer isn't there, say *I couldn't find that in the documents*." |

### Part B – Live: answers that work (~1 min)

| # | Do | Say |
|---|---|---|
| 2 | `python run.py -q "How many credits are required for the Computer Science major?"` | "56 credits, which matches page 7." |
| 3 | `python run.py -q "Who is eligible to take the Capstone project?"` | "A major GPA of 3.5 and an approved application, page 9. Also correct." |
| 4 | `python run.py -q "Who won the 2022 FIFA World Cup?"` | "This one is out of scope. The model knows the answer, but it says it isn't in the documents. That's what we want from a handbook assistant: it shouldn't answer from its own memory." |

### Part C – Live: answers that fail, and why (~2 min)

| # | Do | Say |
|---|---|---|
| 5 | `python run.py -q "What is the difference between graduating with and without honors in CS?" --show-context` | "This is a failure. It says it couldn't find the answer, but page 8 does explain it." |
| 6 | Scroll up to the first printed chunk (p.8). Point at its first line: "two more intermediate or advanced courses to graduate without honors." | "Here's why. Look at the first chunk: it starts mid-sentence. The sentence was cut in half when the text was split into chunks. Only the half about graduating *without* honors was retrieved. The model saw half the information and refused to guess, which is correct behaviour. So this is a **chunking** problem, not a model problem." |
| 7 | `python run.py -q "How often is Computer Networks offered?"` | "This one is worse. It says 'once a semester, page 16', but the course catalogue on page 13 says it's **on holding**. The catalogue row wasn't retrieved, so the model guessed, and a page number makes the wrong answer look trustworthy." |
| 8 | `python run.py -q "What courses are required for the Computer Science major?"` | "This answer is incomplete. It leaves out Capstone I and II, even though that line was in the retrieved text. Its own list adds up to 48 credits, but it still says 56. This is a **generation** error: the information was there, and the model dropped it." |

### Part D – The evaluation (~1.5 min)

| # | Do | Say |
|---|---|---|
| 9 | Open `tests/test_questions.json`, scroll briefly. | "To test it properly, I wrote 18 questions covering requirements, courses, learning outcomes, policies, multi-step and ambiguous questions, and 3 out-of-scope ones. Each has an expected answer and page." |
| 10 | Open `results/SUMMARY.md`, table 1. | "`evaluate.py` ran all 18 questions on three sizes of the same model: 0.5, 1.5 and 3 billion parameters. Retrieval is the same for all three, so the differences come only from the model that writes the answer. The 1.5b model invented a transfer-credit policy, while 3b correctly declined it, so I use 3b as the default." |
| 11 | Open `results/failure_cases_qwen2.5-3b.md`, show the overview table and scroll through 2–3 cases (for example Q09 and Q13). | "I graded the 3b answers by hand: 10 correct, 4 incomplete, 3 incorrect and 1 ambiguous. This file shows each failure with the model's answer, what the handbook says, and why it failed. For example, in Q09 it listed the Core learning outcomes instead of the Major ones, because the two tables are next to each other and lose their structure when the PDF is converted to text. In Q13 it found only the first prerequisite and didn't follow the chain." |
| 12 | Stay on that file. | "In summary, most errors come from how the text is split, or from the small model leaving out what it was given, not from it inventing facts. One question is ambiguous because the handbook contradicts itself: page 6 says 'Applied Mathematics' instead of 'Computer Science'." |

Note: the live answers in Part C match the evaluation run word for word, so you can rely on them.

---

## Video 3 – Task 3: Docker deployment (~3–4 min)

**Goal:** show that anyone can run the whole system with one command, without installing Python or Ollama.

**Setup before recording (not on camera):**

1. Open Docker Desktop and wait until it says **Engine running**. Until then, every `docker` command fails with
   `failed to connect to the docker API`.
2. **Quit the Ollama tray app** (right-click its icon → Quit). This shows that the containers don't use your own Ollama.
3. Open a **new** PowerShell window. You don't need the `.venv`, because Docker doesn't use it. Go to the **repository root**,
   the folder that contains `docker/`:
   ```powershell
   cd "D:\Courses\AY 26-27\Advanced Deep Learning\Final Project\ADL-project"
   ```
   If you run the commands from `source_code`, you'll get `docker-compose.yml ... cannot find the path specified`,
   because there's no `docker` folder inside `source_code`.
4. Stop the containers left over from an earlier run, so the video starts from a clean state:
   ```powershell
   docker compose -f docker/docker-compose.yml down
   ```
   This doesn't delete the volumes, so the models and the index stay downloaded.

| # | Do | Say |
|---|---|---|
| 1 | Open `docker/Dockerfile`. | "The Dockerfile is the recipe for the app image. It starts from Python 3.11, installs the requirements, copies the code, runs as a non-root user and starts Streamlit on port 8501." |
| 2 | Open `docker/docker-compose.yml`. | "Compose runs three containers together. **ollama** is the model server. **model-init** downloads the two models once and then exits. **app** is my chatbot. The handbook folder is mounted, so documents can be swapped without rebuilding. The models and the vector index are kept in named volumes, so they survive restarts." |
| 3 | Run:<br>`docker compose -f docker/docker-compose.yml -f docker/docker-compose.gpu.yml up --build -d` | "This builds the image and starts everything. The second file gives the Ollama container my GPU." |
| 4 | `docker ps` | "The ollama and app containers are running. model-init has already finished." |
| 5 | `docker compose -f docker/docker-compose.yml logs app --tail 15` | "These are the app's logs: Streamlit started on port 8501 inside the container." (If you've opened the page already, you'll also see the index line.) |
| 6 | Open http://localhost:8501 and ask a question. | "The same chatbot, now running entirely inside Docker." |
| 7 | `docker compose -f docker/docker-compose.yml restart app`, wait about 10 s, then **refresh the browser page** (F5) and ask a question. | "Now I restart the app container. That throws away the running container's memory." |
| 8 | `docker compose -f docker/docker-compose.yml logs app --tail 15` | "After the restart, the last line says *Loaded existing index ... 64 chunks*, not *Embedding 64 chunks*. The index was saved in the `vector_store` volume, so it survived the restart and didn't need to be rebuilt. Streamlit only loads the pipeline when someone opens the page, which is why I refreshed the browser first." |
| 9 | `docker compose -f docker/docker-compose.yml down` | "This stops it. Adding `-v` would also delete the volumes." |

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
