# API Contract Guardian

Enforces strict API contracts between frontend and backend systems. Invalid requests are rejected before processing. Invalid responses never leave the server.

---

## Problem

Frontend and backend systems drift apart over time. A field gets renamed, a type changes, an endpoint is restructured — and the mismatch only surfaces at runtime, often in production. This system makes those mismatches fail loudly and immediately, at the boundary.

---

## Architecture

```
Frontend (React)
      ↓
Flask Routes          — thin, request/response handling only
      ↓
Middleware             — STRICT validation layer (before_request / after_request)
      ↓
Service Layer         — business logic (contract_service, log_service)
      ↓
Validator Layer       — deterministic schema checking (no AI)
      ↓
Database              — contracts + validation failure logs
      ↓
AI Layer              — Gemini, assistive only (schema gen + error explanation)
```

---

## Project Structure

```
backend/
  app.py                  — app factory, middleware registration
  config.py               — environment config
  db.py                   — SQLAlchemy + Flask-Migrate init
  models/
    contract.py           — Contract model
    log.py                — ValidationLog model
  routes/
    contract_routes.py    — CRUD for contracts + log listing
    test_routes.py        — test/validate endpoint
    ai_routes.py          — AI schema gen + error explanation
  middleware/
    contract_middleware.py — before_request / after_request hooks
  services/
    contract_service.py   — contract DB operations
    log_service.py        — log DB operations
    ai_service.py         — Gemini integration (constrained)
  validators/
    schema_validator.py   — deterministic payload validation
  tests/
    test_validation.py    — pytest test suite

frontend/
  src/
    api.js                — fetch wrapper
    App.jsx               — tab navigation
    components/
      ContractList.jsx    — list + delete contracts
      CreateContract.jsx  — create contract + AI schema gen
      TestPanel.jsx       — validate payloads against a contract
      LogViewer.jsx       — view validation failure logs
```

---

## Design Decisions

### 1. Middleware as the enforcement layer
Validation runs in `before_request` and `after_request` hooks — not inside route handlers. This means no route can accidentally skip validation. Routes stay thin and focused on response construction.

### 2. Contracts stored in the database
Contracts are not hardcoded. Adding or changing a contract requires no code change. This makes the system resilient to endpoint evolution and allows runtime contract management.

### 3. Deterministic validator — no AI
`schema_validator.py` is pure Python with no external dependencies. It checks required fields and data types. It is the source of truth for correctness. AI is explicitly excluded from this layer.

### 4. AI is constrained and verified
Gemini is called only for schema generation and error explanation. Every AI response is validated by `_validate_schema_structure` before use. If AI fails or returns garbage, the system falls back gracefully. The rest of the system is unaffected.

### 5. Internal routes bypass middleware
Routes under `/contracts`, `/logs`, `/ai`, `/test`, and `/health` are the guardian system itself. They are excluded from contract enforcement to avoid circular validation.

---

## Schema Format

Schemas are JSON objects where each key is a field name:

```json
{
  "name":  { "type": "string",  "required": true  },
  "age":   { "type": "integer", "required": true  },
  "email": { "type": "string",  "required": false }
}
```

Supported types: `string`, `integer`, `float`, `boolean`, `list`, `dict`

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/contracts` | List all contracts |
| POST | `/contracts` | Create a contract |
| DELETE | `/contracts/:id` | Delete a contract |
| GET | `/logs` | List validation failure logs |
| POST | `/test/validate` | Validate a payload against a contract |
| POST | `/ai/generate-schema` | Generate a schema from plain English |
| POST | `/ai/explain-error` | Explain a validation error |
| GET | `/health` | Health check |

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key_here
export DATABASE_URL=sqlite:///api_guardian.db   # or postgresql://...

# Initialize DB
flask --app app db init
flask --app app db migrate -m "initial"
flask --app app db upgrade

# Run
python app.py
```

### Frontend

```bash
cd frontend
cp .env.example .env          # set VITE_API_URL if backend is not on localhost:5000
npm install
npm run dev
```

### Tests

```bash
cd backend
pytest tests/ -v
```

---

## Deployment

- **Backend**: Configure your preferred hosting provider and set required environment variables
- **Frontend**: Configure `VITE_API_URL` to your backend base URL
- **Database**: SQLite for development; choose a managed database if needed in production

---

## AI Usage

See [agents.md](./agents.md) for full AI rules and safety constraints.

**Summary**: AI generates schemas and explains errors. It never validates requests, never writes to the database, and is never trusted without verification. If AI is unavailable, the system continues to function correctly.

---

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| SQLite default | Zero setup for dev | Not suitable for high-concurrency prod |
| Simple schema format (not JSON Schema) | Easy to read and write | Less expressive than full JSON Schema |
| Middleware validates all non-internal routes | Consistent enforcement | Requires contracts to be registered before use |
| AI output validated and stripped | Safe, predictable | AI-generated schemas may lose fields with unknown types |

---

## Risks & Limitations

- **No authentication** — the contract management API is open. Add auth before exposing to the internet.
- **Schema format is custom** — not JSON Schema / OpenAPI. Interop with other tools requires a converter.
- **Response validation rewrites the response** — if a service returns a valid but unexpected shape, it will be blocked. Contracts must be kept up to date.
- **AI schema generation is best-effort** — always review AI-generated schemas before saving.

---

## Extensions

- Add JWT authentication to the contract management API
- Support JSON Schema / OpenAPI as the schema format
- Add a diff view when a contract changes
- Webhook notifications on validation failures
- Per-endpoint validation toggle (warn vs. reject mode)
