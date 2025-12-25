from typing import Dict, List
from app.rag.index import RagIndex

class RagService:
    def __init__(self, docs_folder: str):
        self.index = RagIndex(docs_folder=docs_folder)

    def retrieve(self, query: str, k: int = 4) -> List[dict]:
        return self.index.retrieve(query, k=k)


# tenant-level cache (used by FastAPI, NOT tests)
_RAG_CACHE: Dict[str, RagService] = {}

def get_rag(tenant: dict) -> RagService:
    tid = tenant["tenant_id"]
    if tid not in _RAG_CACHE:
        folder = tenant.get("rag", {}).get("docs_folder", "")
        _RAG_CACHE[tid] = RagService(docs_folder=folder)
    return _RAG_CACHE[tid]
