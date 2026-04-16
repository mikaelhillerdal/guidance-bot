from fastapi import FastAPI
from app.api.routes_chat import router as chat_router
from app.api.routes_planned_educations import router as planned_educations_router

app = FastAPI(title="Guidance Counselor Bot API")
app.include_router(chat_router)
app.include_router(planned_educations_router)
