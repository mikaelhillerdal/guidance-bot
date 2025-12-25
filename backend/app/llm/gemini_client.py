from google import genai
from app.core.config import GOOGLE_API_KEY, MODEL_NAME

_client = genai.Client(api_key=GOOGLE_API_KEY)

def generate(contents, tools=None):
    return _client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config={"tools": tools} if tools else None
    )
