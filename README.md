# DocQA — Ask Your Manuals (demo project)

> **Demo / portfolio project.** The preloaded "Brewline X2" coffee maker manual is a fictional document made for this demo. Uploaded files are private to your browser session and auto-delete after 24 hours.

**Live demo:** <https://doc-qa-bot-twfd.onrender.com> (free hosting: first load can take up to a minute)

Upload PDF manuals, ask questions in plain English, and get short answers that **cite the exact file and page**. Click a citation to open the PDF on that page.

![screenshot](docs/screenshots/1-answer-with-citations.png)

## Case study

**Problem.** Support teams, technicians and customers lose time digging through long PDF manuals. Generic chatbots make things up, and nobody can check where an answer came from.

**What it does.**
- Upload PDFs (or use the preloaded sample) and ask questions in a chat.
- Answers come only from the documents. Every fact has a numbered citation linked to file + page.
- If the answer is not in the documents, it says so instead of guessing.
- Keyword search (BM25) finds exact part numbers and error codes. Optional hybrid mode (BM25 + Gemini embeddings, merged with reciprocal rank fusion) switches on when a Gemini key is set, so loosely worded questions match too.
- Runs without any API key in "search-only" mode, which returns the best passages with citations.
- Demo guard rails: per-session documents, upload size/file limits, hourly question limit per IP.

**Stack.** Python · FastAPI · pypdf · NumPy (local vector store, no database) · Anthropic Claude Haiku (live demo) or Google Gemini (adds embeddings) · vanilla HTML/CSS/JS (no build step) · Docker on Render.

**Result.** One small codebase (~500 lines) that a business can point at its own manuals, SOPs or policy documents. Answers take a few seconds and cost a fraction of a cent per question.

## How it works

```
PDF ──► extract text per page ──► drop headers/footers ──► ~1500-char chunks (page-tagged)
                                                              │
                                    BM25 index  ◄─────────────┤
                                    embeddings (.npy) ◄───────┘   (only with a Gemini key)
question ──► BM25 top-50 (+ vector top-50 ──► rank fusion) ──► top 6 passages
         ──► LLM with "answer only from these, cite [n]" ──► answer + source cards
```

| File | Job |
|---|---|
| `app/rag.py` | PDF ingest, chunking, BM25 + optional vector hybrid search |
| `app/llm.py` | Claude / Gemini calls, embeddings, prompt, search-only fallback |
| `app/main.py` | FastAPI routes, sessions, limits, sample preload |
| `static/` | Chat UI (no framework) |
| `samples/make_sample.py` | Builds the fictional sample manual PDF |

## Run locally (Windows)

```powershell
cd "E:\AI Portfolio\doc-qa-bot"
.\run.ps1
```

First run makes a `.venv`, installs packages and creates `.env`. Put one key in `.env`:

```
ANTHROPIC_API_KEY=your-key-here
# or GEMINI_API_KEY=your-key-here  (also turns on hybrid search)
```

Restart, then open <http://localhost:8000>. No key? It still runs in search-only mode.

**Local test with a Claude subscription (no API key):** if the `claude` CLI is installed and logged in, set `LLM_PROVIDER=claude-cli` in `.env`. Answers go through Claude Haiku via the CLI (~8–12 s each). Local only — the deployed demo needs `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`.

Mac/Linux: `python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/uvicorn app.main:app --port 8000`

## Deploy (free, Render)

1. Push the project to a GitHub repo.
2. render.com → **New → Blueprint** → pick the repo (it reads `render.yaml`, free plan).
3. Enter `ANTHROPIC_API_KEY` when asked → **Deploy Blueprint**. Build takes 3–5 min.
4. The free plan sleeps after 15 min idle (first visit after that takes ~1 min). To keep it awake, ping `https://<your-app>.onrender.com/api/status` every 10 min with a free cron service such as cron-job.org.

Set a monthly spend limit on the API key so a public demo can never run up a bill.

## Settings (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | – | Claude key (answers) |
| `GEMINI_API_KEY` | – | Gemini key (answers + embeddings); used first if set |
| `CLAUDE_MODEL` | `claude-haiku-5-5` | Answer model when using Claude |
| `GEMINI_MODEL` | `gemini-flash-latest` | Answer model when using Gemini |
| `ASKS_PER_HOUR` | 40 | Questions per IP per hour |
| `MAX_UPLOAD_MB` / `MAX_FILES_PER_SESSION` | 10 / 3 | Upload limits |

## Adapting it for a real client

- Swap the sample manual for their PDFs (or load a folder at startup).
- Add login, a real vector DB (pgvector, Qdrant) for thousands of documents, OCR for scanned PDFs.
- Embed the chat as a widget on their site, or connect it to Slack / WhatsApp / a help desk.
- For private company data, use a paid API tier (no training on data) and keep files in their own cloud.

---
Portfolio demo project. Not affiliated with any real appliance brand.
