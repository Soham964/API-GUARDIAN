# agents.md — AI Usage Rules & Safety Constraints

## Role of AI in This System

AI (Google Gemini) is an **assistive tool only**. It is never in the critical path of correctness.

## What AI Is Allowed To Do

| Task | Allowed |
|------|---------|
| Generate a JSON schema from a description | ✅ |
| Explain a validation error in plain language | ✅ |
| Validate incoming requests | ❌ |
| Modify the database | ❌ |
| Bypass middleware | ❌ |
| Be trusted without verification | ❌ |

## Safety Constraints (Enforced in Code)

1. **All AI output is validated** before use (`_validate_schema_structure` in `ai_service.py`).
2. **AI never touches the database** — only `contract_service.py` and `log_service.py` write to DB.
3. **AI never validates requests** — `schema_validator.py` is deterministic and AI-free.
4. **If AI fails, the system continues** — every AI call has a safe fallback.
5. **AI output is stripped of invalid fields** — unknown types or malformed fields are removed.

## Prompt Rules

### Schema Generation
- Output ONLY valid JSON.
- No explanations, no markdown, no code fences.
- Each key = field name; value = `{ "type": "...", "required": true|false }`.

### Error Explanation
- Convert technical error to 1–2 sentence plain English.
- Be actionable — tell the developer what to fix.

## Coding Standards

- AI logic lives exclusively in `services/ai_service.py`.
- No AI imports in `validators/`, `middleware/`, or `models/`.
- All AI calls are wrapped in try/except with logged warnings.
- AI responses are never returned raw to the client.

## Risk Acknowledgment

- AI may generate incorrect schemas — always review before saving.
- AI explanations are informational only — the authoritative error is the validator output.
- If `GEMINI_API_KEY` is missing, AI features return a clear error; the rest of the system is unaffected.
