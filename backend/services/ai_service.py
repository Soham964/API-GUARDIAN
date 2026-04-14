"""
AI Service — Groq integration via OpenAI-compatible API.
Model: llama-3.3-70b-versatile

SAFETY RULES (enforced here):
- AI is used ONLY for schema generation and error explanation.
- AI output is ALWAYS validated before use.
- AI never touches the database directly.
- AI never validates requests (that is the validator's job).
- If AI fails or returns invalid output, a safe fallback is returned.
"""

import json
import re
from flask import current_app


def _generate(prompt: str) -> str:
    """Call Groq and return the text response."""
    api_key = current_app.config.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def generate_schema(description: str) -> dict:
    """
    Ask Grok to generate a JSON schema from a natural language description.
    Output is validated before returning. Falls back to error dict on failure.
    """
    prompt = (
        "You are a JSON schema generator. "
        "Output ONLY a valid JSON object. No explanation, no markdown, no code blocks. "
        "Each key is a field name. Each value is an object with 'type' "
        "(one of: string, integer, float, boolean, list, dict) and 'required' (true or false). "
        f"Generate a schema for: {description}"
    )
    try:
        raw = _generate(prompt)
        # Strip markdown code fences if present
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        schema = json.loads(raw)
        return _validate_schema_structure(schema)
    except Exception as e:
        current_app.logger.warning(f"AI schema generation failed: {e}")
        return {"error": f"AI unavailable: {str(e)}"}


def explain_error(error_message: str) -> str:
    """
    Ask Grok to explain a validation error in plain language.
    Falls back to the original error message if AI fails.
    """
    prompt = (
        "You are an API error explainer. "
        "Convert this technical validation error into a simple, friendly explanation "
        "that a developer can act on. Be concise (1-2 sentences). "
        f"Error: {error_message}"
    )
    try:
        explanation = _generate(prompt)
        return explanation if explanation else error_message
    except Exception as e:
        current_app.logger.warning(f"AI error explanation failed: {e}")
        return error_message  # Safe fallback: return original error


def _validate_schema_structure(schema: dict) -> dict:
    """
    Validate that AI-generated schema has the correct structure.
    Strips any fields that don't conform. Never trusts AI blindly.
    """
    valid_types = {"string", "integer", "float", "boolean", "list", "dict"}
    cleaned = {}
    for field, rules in schema.items():
        if not isinstance(rules, dict):
            continue
        field_type = rules.get("type")
        if field_type not in valid_types:
            continue
        cleaned[field] = {
            "type": field_type,
            "required": bool(rules.get("required", True)),
        }
    return cleaned
