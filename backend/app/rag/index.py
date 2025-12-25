# rag/index.py
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Dict
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
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

def load_documents_from_folder(folder: Path) -> List[Tuple[str, str]]:
    docs: List[Tuple[str, str]] = []
    if not folder.exists():
        return docs
    for p in folder.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in {".txt", ".md"}:
            text = p.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                docs.append((str(p), text))
    return docs

class RagIndex:
    def __init__(self, docs_folder: str):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.docs_folder = docs_folder
        self.index, self.chunks, self.meta = self._build()

    def _build(self):
        docs = load_documents_from_folder(Path(self.docs_folder))
        chunks: List[str] = []
        meta: List[Dict] = []
        for src, text in docs:
            for i, c in enumerate(chunk_text(text)):
                chunks.append(c)
                meta.append({"source": src, "chunk": i})

        dim = self.embedder.get_sentence_embedding_dimension()
        index = faiss.IndexFlatIP(dim)

        if chunks:
            emb = self.embedder.encode(chunks, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
            index.add(emb)

        return index, chunks, meta

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
        q = self.embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        scores, ids = self.index.search(q, k)
        out = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
            if idx < 0 or idx >= len(self.chunks):
                continue
            out.append({
                "score": float(score),
                "text": self.chunks[idx],
                "source": self.meta[idx]["source"],
                "chunk": self.meta[idx]["chunk"],
            })
        return out
