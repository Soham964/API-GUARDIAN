# API Contract Guardian

A runtime API contract enforcement system. Registers request and response schemas for endpoints, then validates every request and response against them — rejecting mismatches before they reach business logic or leave the server.

**Live demo:** http://3.110.190.226

---

## What It Does

Frontend and backend systems drift apart over time. A field gets renamed, a type changes, an endpoint is restructured — and the mismatch only surfaces at runtime, often in production.

API Contract Guardian makes those mismatches **fail loudly and immediately**, at the boundary:

- Register a contract (endpoint + method + request schema + response schema)
- Every incoming request to that endpoint is validated against the request schema — invalid requests are rejected with a structured error before any business logic runs
- Every outgoing response is validated against the response schema — invalid responses are blocked with a 500 before reaching the client
- All failures are logged with full details for debugging

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite |
| Backend | Flask 3, Python 3.12 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy + Flask-Migrate |
| AI | Groq (llama-3.1-8b) via OpenAI-compatible API |
| Server | Gunicorn + Nginx |
| Hosting | AWS EC2 (t3.micro) |

---

## Architecture

```
Frontend (React)
      ↓
Nginx                 — serves frontend, proxies API routes to Flask
      ↓
Flask Routes          — thin, request/response handling only
      ↓
Middleware            — STRICT validation layer (before_request / after_request)
      ↓
Service Layer         — business logic (contract_service, log_service)
      ↓
Validator Layer       — deterministic schema checking (no AI)
      ↓
Database              — contracts + validation failure logs
      ↓
AI Layer              — Groq, assistive only (schema gen + error explanation)
```

---

## Project Structure

```
backend/
  app.py                    — app factory, middleware registration
  config.py                 — environment config
  db.py                     — SQLAlchemy + Flask-Migrate init
  models/
    contract.py             — Contract model
    log.py                  — ValidationLog model
  routes/
    contract_routes.py      — CRUD for contracts + log listing
    test_routes.py          — test/validate endpoint
    ai_routes.py            — AI schema generation + error explanation
  middleware/
    contract_middleware.py  — before_request / after_request enforcement hooks
  services/
    contract_service.py     — contract DB operations
    log_service.py          — log DB operations
    ai_service.py           — Groq AI integration (constrained, assistive only)
  validators/
    schema_validator.py     — deterministic payload validation (no AI)
  tests/
    test_validation.py      — pytest test suite

frontend/
  src/
    api.js                  — fetch wrapper
    App.jsx                 — tab navigation
    components/
      ContractList.jsx      — list + delete contracts
      CreateContract.jsx    — create contract form + AI schema generator
      LogViewer.jsx         — view validation failure logs

deploy/
  setup.sh                  — one-time EC2 setup script
  update.sh                 — pull latest code and restart services
  api-guardian.service      — systemd service definition for gunicorn
  nginx.conf                — nginx config (frontend + API proxy)
```

---

## Key Design Decisions

**Middleware as the enforcement layer** — Validation runs in `before_request` and `after_request` hooks, not inside route handlers. No route can accidentally skip validation. Routes stay thin.

**Contracts stored in the database** — Not hardcoded. Adding or changing a contract requires no code change, no redeploy. Managed at runtime through the UI.

**Deterministic validator, no AI** — `schema_validator.py` is pure Python with zero external dependencies. It is the source of truth for correctness. AI is explicitly excluded from this layer.

**AI is constrained and verified** — AI is used only for schema generation and error explanation. Every AI response is validated by `_validate_schema_structure` before use. If AI fails, the system falls back gracefully and continues working.

**Internal routes bypass enforcement** — Routes under `/contracts`, `/logs`, `/ai`, `/test`, and `/health` are the guardian system itself. They are excluded from contract enforcement to avoid circular validation.

---

## Schema Format

```json
{
  "name":  { "type": "string",  "required": true  },
  "age":   { "type": "integer", "required": false },
  "email": { "type": "string",  "required": true  }
}
```

Supported types: `string`, `integer`, `float`, `boolean`, `list`, `dict`

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/contracts` | List all registered contracts |
| `POST` | `/contracts` | Register a new contract |
| `DELETE` | `/contracts/:id` | Delete a contract |
| `GET` | `/logs` | List validation failure logs |
| `POST` | `/test/validate` | Validate a payload against a contract |
| `POST` | `/ai/generate-schema` | Generate a schema from plain English |
| `POST` | `/ai/explain-error` | Explain a validation error in plain English |
| `GET` | `/health` | Health check |

---

## Local Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env
cp .env.example .env          # set GROQ_API_KEY and DATABASE_URL

# Run
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies API calls to `http://localhost:5000` by default.

### Tests

```bash
cd backend
pytest tests/ -v
```

---

## Production Deployment (AWS EC2)

The app runs on a single EC2 t3.micro instance with Nginx + Gunicorn.

**First-time setup on a fresh Ubuntu 22.04 instance:**

```bash
git clone https://github.com/Soham964/API-GUARDIAN.git /home/ubuntu/app
cd /home/ubuntu/app
bash deploy/setup.sh
```

Then edit `/home/ubuntu/app/backend/.env` with your real credentials and restart:

```bash
sudo systemctl restart api-guardian
```

**To deploy updates:**

```bash
bash /home/ubuntu/app/deploy/update.sh
```

---

## AI Usage

See [agents.md](./agents.md) for full AI rules and safety constraints.

AI generates schemas from plain English descriptions and explains validation errors in human-readable terms. It never validates requests, never writes to the database, and is never trusted without verification. If AI is unavailable, the rest of the system is completely unaffected.

---

## Limitations & Known Tradeoffs

| Area | Note |
|------|------|
| Authentication | The contract management API is open — add auth before exposing to the internet |
| Schema format | Custom format, not JSON Schema / OpenAPI — not directly interoperable with other tooling |
| Response validation | Contracts must be kept up to date — a valid but unexpected response shape will be blocked |
| AI generation | Best-effort — always review AI-generated schemas before saving |
| SQLite | Fine for development and low-traffic production; switch to PostgreSQL for higher concurrency |

---

## Possible Extensions

- JWT authentication on the contract management API
- JSON Schema / OpenAPI import and export
- Diff view when a contract is updated
- Webhook notifications on validation failures
- Per-endpoint warn vs. reject mode toggle
- Contract versioning
