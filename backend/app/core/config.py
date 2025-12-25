from dotenv import load_dotenv
import os

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is missing")
