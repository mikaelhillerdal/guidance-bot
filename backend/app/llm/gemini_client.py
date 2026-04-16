from google import genai
from app.core.config import GOOGLE_API_KEY, MODEL_NAME

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not GOOGLE_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Configure it in your environment.")
    _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

def generate(contents, tools=None):
    client = _get_client()
    return client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config={"tools": tools} if tools else None
    )
