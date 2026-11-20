"""LLM + embedding calls. Gemini first (cheap, free tier), Claude as backup.

No key set? The app still runs in "search-only" mode: it returns the best
matching passages with citations, no generated answer.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

import httpx
import numpy as np

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
TIMEOUT = httpx.Timeout(60.0)

SYSTEM = """You answer questions using ONLY the numbered document excerpts given.
Rules:
- Cite every fact with its excerpt number in square brackets, like [1] or [2][3].
- If the excerpts do not contain the answer, say: "I couldn't find that in the uploaded documents." Then, if useful, say what the documents do cover.
- Be concise and practical. Use numbered steps for procedures and bullets for lists.
- Write in clear, complete, friendly sentences for a customer-facing support assistant (no slang, no telegraphic shorthand). This style rule overrides any other style instructions.
- Never invent part numbers, values, or steps that are not in the excerpts."""


def _gemini_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def provider() -> str:
    # Local dev only: route answers through the Claude Code CLI (uses your
    # Claude subscription, no API key). Not for deployment.
    if os.getenv("LLM_PROVIDER") == "claude-cli":
        return "claude-cli"
    if _gemini_key():
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude"
    return "none"


def model_name() -> str:
    p = provider()
    if p == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    if p == "claude":
        return os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
    if p == "claude-cli":
        return "claude-haiku"
    return "search-only"


def embed(texts: list[str], task: str) -> np.ndarray | None:
    """Return L2-normalised embeddings, or None if no Gemini key / call fails."""
    key = _gemini_key()
    if not key or os.getenv("DISABLE_EMBEDDINGS") == "1":
        return None
    model = os.getenv("EMBED_MODEL", "gemini-embedding-001")
    dims = int(os.getenv("EMBED_DIMS", "768"))
    out: list[list[float]] = []
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            for i in range(0, len(texts), 100):  # API batch limit
                batch = texts[i:i + 100]
                r = c.post(
                    f"{GEMINI_URL}/models/{model}:batchEmbedContents",
                    headers={"x-goog-api-key": key},
                    json={"requests": [{
                        "model": f"models/{model}",
                        "content": {"parts": [{"text": t}]},
                        "taskType": task,
                        "outputDimensionality": dims,
                    } for t in batch]},
                )
                r.raise_for_status()
                out.extend(e["values"] for e in r.json()["embeddings"])
    except Exception as e:  # embeddings are optional; BM25 still works
        print(f"[embed] skipped: {e}")
        return None
    v = np.asarray(out, dtype=np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


def _context(passages: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] (file: {p['file']}, page {p['page']})\n{p['text']}"
        for i, p in enumerate(passages, start=1)
    )


def answer(question: str, passages: list[dict], history: list[dict]) -> str:
    p = provider()
    if p == "none":
        return ("**Search-only mode** (no LLM key set). Most relevant passages:\n\n" +
                "\n\n".join(f"[{i}] {' '.join(s['text'].split())[:280]}…"
                            for i, s in enumerate(passages[:3], start=1)))
    hist = "\n".join(f"{m['role']}: {m['content'][:500]}" for m in history[-4:])
    prompt = (f"Earlier conversation (for context only):\n{hist}\n\n" if hist else "") + \
        f"Document excerpts:\n{_context(passages)}\n\nQuestion: {question}"
    if p == "claude-cli":
        r = subprocess.run(
            [shutil.which("claude") or "claude", "-p", "--model", "haiku",
             "--system-prompt", SYSTEM, "--tools", ""],
            input=prompt, capture_output=True, text=True, encoding="utf-8",
            timeout=180, cwd=tempfile.gettempdir(),
        )
        if r.returncode != 0 or not r.stdout.strip():
            raise RuntimeError(f"claude CLI failed: {r.stderr[:300]}")
        return r.stdout.strip()
    if p == "gemini":
        r = httpx.post(
            f"{GEMINI_URL}/models/{model_name()}:generateContent",
            headers={"x-goog-api-key": _gemini_key()},
            json={"systemInstruction": {"parts": [{"text": SYSTEM}]},
                  "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        return "".join(x.get("text", "") for x in parts if not x.get("thought")).strip()
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"},
        json={"model": model_name(), "max_tokens": 1024, "system": SYSTEM,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"]).strip()


def cited_numbers(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"\[(\d{1,2})\]", text)}
