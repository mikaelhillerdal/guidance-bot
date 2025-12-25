from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf_file(path: Path) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def load_documents_from_folder(folder: Path) -> List[Tuple[str, str]]:
    docs: List[Tuple[str, str]] = []
    if not folder.exists():
        return docs

    for p in folder.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()

        text = ""
        if ext in {".txt", ".md"}:
            text = read_text_file(p)
        elif ext == ".pdf":
            text = read_pdf_file(p)

        text = (text or "").strip()
        if text:
            docs.append((str(p), text))
    return docs


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


class RagIndex:
    def __init__(self, docs_folder: str):
        self.docs_folder = docs_folder
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index, self.chunks, self.meta = self._build()

    def _build(self):
        docs = load_documents_from_folder(Path(self.docs_folder))

        chunks: List[str] = []
        meta: List[Dict] = []

        for source, text in docs:
            for i, chunk in enumerate(chunk_text(text)):
                chunks.append(chunk)
                meta.append({"source": source, "chunk": i})

        dim = self.embedder.get_sentence_embedding_dimension()
        index = faiss.IndexFlatIP(dim)

        if chunks:
            emb = self.embedder.encode(
                chunks, convert_to_numpy=True, normalize_embeddings=True
            ).astype(np.float32)
            index.add(emb)

        return index, chunks, meta

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        if self.index.ntotal == 0:
            return []

        q = self.embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        scores, ids = self.index.search(q, k)

        results: List[Dict] = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
            if idx < 0 or idx >= len(self.chunks):
                continue
            results.append({
                "score": float(score),
                "text": self.chunks[idx],
                "source": self.meta[idx]["source"],
                "chunk": self.meta[idx]["chunk"],
            })
        return results
