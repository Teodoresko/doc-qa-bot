"""Ingest PDFs, chunk by page, and search with hybrid BM25 + vector retrieval.

Each document lives in its own folder:
    <store>/<doc_id>/source.pdf     original file
    <store>/<doc_id>/chunks.json    text chunks with file name + page number
    <store>/<doc_id>/vectors.npy    optional embeddings (one row per chunk)
"""
from __future__ import annotations

import json
import math
import re
import shutil
import uuid
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from pypdf import PdfReader

from . import llm

CHUNK_CHARS = 1500
OVERLAP_CHARS = 200
_WORD = re.compile(r"[a-z0-9]+")
_STOP = set(
    "a an the and or of to in on for with is are was be by it this that as at from "
    "you your can will do does how what when which who why if not no".split()
)


def _stem(w: str) -> str:
    """Very light stemmer: descaling / descaled / descale -> descal."""
    if len(w) > 4 and not w[0].isdigit():
        for suf in ("ing", "ed", "es", "s", "e"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                return w[: -len(suf)]
    return w


def tokenize(text: str) -> list[str]:
    return [_stem(w) for w in _WORD.findall(text.lower()) if w not in _STOP]


@dataclass
class Chunk:
    doc_id: str
    file: str
    page: int
    text: str


def _split_page(text: str) -> list[str]:
    """Split one page into overlapping chunks on paragraph/sentence edges."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) <= CHUNK_CHARS:
        return [text] if text else []
    parts, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            cut = max(text.rfind("\n", start, end), text.rfind(". ", start, end))
            if cut > start + CHUNK_CHARS // 2:
                end = cut + 1
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - OVERLAP_CHARS, start + 1)
    return [p for p in parts if p]


def ingest_pdf(src: Path, store: Path, display_name: str, max_pages: int = 80) -> dict:
    """Copy a PDF into the store, extract + chunk text, embed if a key is set."""
    reader = PdfReader(str(src))
    if len(reader.pages) > max_pages:
        raise ValueError(f"PDF has {len(reader.pages)} pages; demo limit is {max_pages}.")
    doc_id = uuid.uuid4().hex[:12]
    folder = store / doc_id
    folder.mkdir(parents=True)
    shutil.copy(src, folder / "source.pdf")

    texts = [page.extract_text() or "" for page in reader.pages]
    # Drop running headers/footers: lines repeated on most pages, or "Page N".
    seen: Counter = Counter()
    for t in texts:
        seen.update({ln.strip() for ln in t.splitlines() if ln.strip()})
    repeat = {ln for ln, n in seen.items() if len(texts) > 2 and n >= 0.6 * len(texts)}
    chunks: list[Chunk] = []
    for i, t in enumerate(texts, start=1):
        t = "\n".join(ln for ln in t.splitlines()
                      if ln.strip() not in repeat and not re.fullmatch(r"\s*(page\s*)?\d+\s*", ln, re.I))
        for part in _split_page(t):
            chunks.append(Chunk(doc_id, display_name, i, part))
    if not chunks:
        shutil.rmtree(folder)
        raise ValueError("No text found. Scanned PDFs need OCR (not in this demo).")

    meta = {"doc_id": doc_id, "file": display_name, "pages": len(reader.pages),
            "chunks": [asdict(c) for c in chunks]}
    (folder / "chunks.json").write_text(json.dumps(meta), encoding="utf-8")

    vecs = llm.embed([c.text for c in chunks], task="RETRIEVAL_DOCUMENT")
    if vecs is not None:
        np.save(folder / "vectors.npy", vecs)
    return {"doc_id": doc_id, "file": display_name, "pages": len(reader.pages),
            "chunks": len(chunks), "vectors": vecs is not None}


class Index:
    """In-memory search over every document in one or more store folders."""

    def __init__(self, folders: list[Path]):
        self.chunks: list[Chunk] = []
        self.docs: list[dict] = []
        vec_rows: list[np.ndarray | None] = []
        for store in folders:
            if not store.exists():
                continue
            for d in sorted(store.iterdir()):
                meta_path = d / "chunks.json"
                if not meta_path.exists():
                    continue
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                cs = [Chunk(**c) for c in meta["chunks"]]
                vp = d / "vectors.npy"
                v = np.load(vp) if vp.exists() else None
                if v is not None and len(v) != len(cs):
                    v = None
                self.chunks.extend(cs)
                vec_rows.extend(list(v) if v is not None else [None] * len(cs))
                self.docs.append({"doc_id": meta["doc_id"], "file": meta["file"],
                                  "pages": meta["pages"], "dir": str(d)})
        # Vector search only if every chunk has a vector of the same size.
        self.vectors = None
        if vec_rows and all(r is not None for r in vec_rows):
            if len({r.shape for r in vec_rows}) == 1:
                self.vectors = np.vstack(vec_rows)
        self._build_bm25()

    def _build_bm25(self) -> None:
        self.tf = [Counter(tokenize(c.text)) for c in self.chunks]
        self.lens = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.lens) / len(self.lens)) if self.lens else 1.0
        df: Counter = Counter()
        for t in self.tf:
            df.update(t.keys())
        n = len(self.chunks)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def _bm25(self, query: str, k1: float = 1.4, b: float = 0.75) -> np.ndarray:
        q = tokenize(query)
        scores = np.zeros(len(self.chunks))
        for i, tf in enumerate(self.tf):
            s = 0.0
            for w in q:
                f = tf.get(w)
                if f:
                    s += self.idf[w] * f * (k1 + 1) / (f + k1 * (1 - b + b * self.lens[i] / self.avg))
            scores[i] = s
        return scores

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        bm = self._bm25(query)
        rankings = [np.argsort(-bm)]
        if self.vectors is not None:
            qv = llm.embed([query], task="RETRIEVAL_QUERY")
            if qv is not None and qv.shape[1] == self.vectors.shape[1]:
                rankings.append(np.argsort(-(self.vectors @ qv[0])))
        # Reciprocal rank fusion: robust way to merge keyword + meaning search.
        fused = np.zeros(len(self.chunks))
        for order in rankings:
            for rank, idx in enumerate(order[:50]):
                fused[idx] += 1.0 / (60 + rank)
        # A keyword-only hit list with zero overlap is noise; drop it.
        if len(rankings) == 1:
            fused[bm <= 0] = 0
        top = [i for i in np.argsort(-fused)[:k] if fused[i] > 0]
        return [(self.chunks[i], float(fused[i])) for i in top]
