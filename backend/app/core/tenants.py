import json
from pathlib import Path
from typing import Any, Dict
from fastapi import HTTPException

TENANT_DIR = Path("./tenants")
_TENANTS: Dict[str, Dict[str, Any]] = {}

def load_tenant(tenant_id: str) -> Dict[str, Any]:
    if tenant_id in _TENANTS:
        return _TENANTS[tenant_id]

    path = TENANT_DIR / f"{tenant_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown tenant: {tenant_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    _TENANTS[tenant_id] = data
    return data
