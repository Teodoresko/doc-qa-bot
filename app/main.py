"""FastAPI app: upload PDFs, ask questions, get answers that cite file + page."""
from __future__ import annotations

import os
import re
import shutil
import tempfile
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import llm, rag  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.getenv("DATA_DIR", ROOT / "data"))
SAMPLE_SRC = ROOT / "samples"
SAMPLE_STORE = DATA / "sample"
SESSIONS = DATA / "sessions"

MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_FILES = int(os.getenv("MAX_FILES_PER_SESSION", "3"))
ASKS_PER_HOUR = int(os.getenv("ASKS_PER_HOUR", "40"))
SESSION_TTL_H = 24
_SID = re.compile(r"^[a-f0-9-]{8,40}$")

app = FastAPI(title="DocQA Demo")
_index_cache: dict[str, rag.Index] = {}
_asks: dict[str, deque] = defaultdict(deque)


def _build_sample() -> None:
    """Index the bundled sample manual(s). Re-index if a key appeared since."""
    has_docs = SAMPLE_STORE.exists() and any(SAMPLE_STORE.iterdir())
    has_vecs = has_docs and any(SAMPLE_STORE.glob("*/vectors.npy"))
    if has_docs and (has_vecs or llm.provider() != "gemini"):
        return
    shutil.rmtree(SAMPLE_STORE, ignore_errors=True)
    SAMPLE_STORE.mkdir(parents=True)
    for pdf in sorted(SAMPLE_SRC.glob("*.pdf")):
        print("[sample] indexed", rag.ingest_pdf(pdf, SAMPLE_STORE, pdf.name))


@asynccontextmanager
async def _lifespan(_app):
    SESSIONS.mkdir(parents=True, exist_ok=True)
    _build_sample()
    print(f"[llm] provider={llm.provider()} model={llm.model_name()}")
    yield


app.router.lifespan_context = _lifespan


def _session_dir(sid: str | None) -> Path | None:
    if not sid:
        return None
    if not _SID.match(sid):
        raise HTTPException(400, "Bad session id.")
    return SESSIONS / sid


def _index(sid: str | None) -> rag.Index:
    key = sid or "_sample"
    if key not in _index_cache:
        folders = [SAMPLE_STORE]
        sd = _session_dir(sid)
        if sd:
            folders.append(sd)
        _index_cache[key] = rag.Index(folders)
    return _index_cache[key]


def _cleanup_old_sessions() -> None:
    cutoff = time.time() - SESSION_TTL_H * 3600
    for d in SESSIONS.iterdir():
        if d.is_dir() and d.stat().st_mtime < cutoff:
            shutil.rmtree(d, ignore_errors=True)
            _index_cache.pop(d.name, None)


def _rate_limit(ip: str) -> None:
    q, now = _asks[ip], time.time()
    while q and q[0] < now - 3600:
        q.popleft()
    if len(q) >= ASKS_PER_HOUR:
        raise HTTPException(429, "Demo limit reached for this hour. Try again later.")
    q.append(now)


@app.get("/api/status")
def status(x_session: str | None = Header(default=None)):
    idx = _index(x_session)
    sample_ids = {d.name for d in SAMPLE_STORE.iterdir()} if SAMPLE_STORE.exists() else set()
    return {
        "provider": llm.provider(),
        "model": llm.model_name(),
        "vector_search": idx.vectors is not None,
        "limits": {"max_mb": MAX_MB, "max_files": MAX_FILES},
        "docs": [{"doc_id": d["doc_id"], "file": d["file"], "pages": d["pages"],
                  "sample": d["doc_id"] in sample_ids} for d in idx.docs],
    }


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), x_session: str | None = Header(default=None)):
    sd = _session_dir(x_session)
    if not sd:
        raise HTTPException(400, "Missing session id.")
    name = Path(file.filename or "upload.pdf").name
    if not name.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    sd.mkdir(parents=True, exist_ok=True)
    if sum(1 for _ in sd.iterdir()) >= MAX_FILES:
        raise HTTPException(400, f"Demo limit: {MAX_FILES} files. Remove one first.")
    data = await file.read()
    if len(data) > MAX_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large (limit {MAX_MB} MB).")
    _cleanup_old_sessions()
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "in.pdf"
        p.write_bytes(data)
        try:
            info = rag.ingest_pdf(p, sd, name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception:
            raise HTTPException(400, "Could not read that PDF.")
    _index_cache.pop(x_session, None)
    return info


@app.delete("/api/docs/{doc_id}")
def delete_doc(doc_id: str, x_session: str | None = Header(default=None)):
    sd = _session_dir(x_session)
    target = sd / doc_id if sd else None
    if not target or not re.fullmatch(r"[a-f0-9]{12}", doc_id) or not target.exists():
        raise HTTPException(404, "Not found (sample docs can't be removed).")
    shutil.rmtree(target)
    _index_cache.pop(x_session, None)
    return {"ok": True}


@app.get("/api/file/{doc_id}")
def get_file(doc_id: str, session: str | None = None):
    if not re.fullmatch(r"[a-f0-9]{12}", doc_id):
        raise HTTPException(404)
    for base in [SAMPLE_STORE, _session_dir(session)]:
        if base and (base / doc_id / "source.pdf").exists():
            return FileResponse(base / doc_id / "source.pdf", media_type="application/pdf")
    raise HTTPException(404)


class Ask(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    history: list[dict] = []


@app.post("/api/ask")
def ask(body: Ask, request: Request, x_session: str | None = Header(default=None)):
    _rate_limit(request.client.host if request.client else "?")
    t0 = time.time()
    hits = _index(x_session).search(body.question, k=6)
    if not hits:
        return {"answer": "I couldn't find anything about that in the documents. "
                          "Try other words, or upload a related PDF.",
                "sources": [], "ms": int((time.time() - t0) * 1000)}
    passages = [{"n": i, "doc_id": c.doc_id, "file": c.file, "page": c.page, "text": c.text}
                for i, (c, _) in enumerate(hits, start=1)]
    try:
        text = llm.answer(body.question, passages, body.history)
    except Exception as e:
        print("[llm] error:", e)
        raise HTTPException(502, "The AI model did not respond. Please try again.")
    used = llm.cited_numbers(text)
    sources = [p for p in passages if p["n"] in used] or passages[:3]
    return {"answer": text, "sources": sources, "model": llm.model_name(),
            "ms": int((time.time() - t0) * 1000)}


@app.middleware("http")
async def _no_stale_ui(request: Request, call_next):
    resp = await call_next(request)
    if not request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-cache"  # revalidate UI after each deploy
    return resp


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
