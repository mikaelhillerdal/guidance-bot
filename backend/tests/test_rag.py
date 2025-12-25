# tests/test_rag.py
from app.rag.index import RagService

def test_rag_empty():
    rag = RagService("nonexistent")
    assert rag.retrieve("hej") == []
