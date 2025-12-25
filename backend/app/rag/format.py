from typing import List, Dict

def format_rag(snips: List[Dict]) -> str:
    if not snips:
        return ""
    return "\n\n---\n\n".join(
        f"Source: {s['source']} (chunk {s['chunk']})\n{s['text']}"
        for s in snips
    )
