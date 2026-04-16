import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from app.api.routes_chat import router as chat_router
from app.api.routes_planned_educations import router as planned_educations_router

app = FastAPI(title="Guidance Counselor Bot API")

_raw = os.getenv("CORS_ORIGINS", "")
_allowed = {o.strip() for o in _raw.split(",") if o.strip()}

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    allow_origin = origin if (_allowed and origin in _allowed) else "*"

    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": allow_origin,
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Tenant",
                "Access-Control-Max-Age": "600",
            },
        )

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = allow_origin
    return response

app.include_router(chat_router)
app.include_router(planned_educations_router)
