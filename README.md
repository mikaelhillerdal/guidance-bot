# guidance-bot

PoC chatbot for school guidance with:
- **Backend:** FastAPI + Gemini + Skolverket/Alvis integrations
- **Frontend:** Next.js UI

## 1) Local PoC deployment with Docker Compose

### Prerequisites
- Docker + Docker Compose
- A valid Gemini API key

### Start
```bash
export GEMINI_API_KEY="your-key-here"
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Backend docs: http://localhost:8000/docs

## 2) Run without Docker

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 3) PoC production checklist (real-life pilot)

Before deploying to real users, do at least this:

1. **Secrets**
   - Store `GEMINI_API_KEY` in a secret manager (not in git).
2. **CORS + domain hardening**
   - Restrict frontend origin(s) and host behind a real domain/TLS.
3. **Observability**
   - Add request IDs, error logging, uptime checks, and basic dashboards.
4. **Rate limiting**
   - Add per-IP and per-tenant limits to protect API costs.
5. **Safety controls**
   - Keep moderation/guardrails and a fallback response for tool/API failures.
6. **Data governance**
   - Avoid storing unnecessary personal data in logs/conversation history.
7. **Tenant config management**
   - Validate `tenants/*.json` in CI before deployment.

## 4) API used by the current frontend

- `POST /planned-educations/search`
  - body:
    ```json
    {
      "municipalityCode": "0486",
      "educationForm": "komvux",
      "question": "What starts next month?"
    }
    ```

## 5) Notes

- In the UI, if **Use mock data** is enabled, frontend will not call backend.
- For a real-life PoC, disable mock mode in UI and verify that backend/network egress to Skolverket is allowed.
