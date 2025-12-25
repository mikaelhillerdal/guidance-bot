# backend/app/main.py
from fastapi import FastAPI
from app.api.routes_chat import router as chat_router

app = FastAPI(title="Guidance Bot API")

app.include_router(chat_router)
