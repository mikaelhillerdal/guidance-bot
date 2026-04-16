import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_chat import router as chat_router
from app.api.routes_planned_educations import router as planned_educations_router

app = FastAPI(title="Guidance Counselor Bot API")

_raw = os.getenv("CORS_ORIGINS", "")
_origins = [o.strip() for o in _raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(planned_educations_router)
