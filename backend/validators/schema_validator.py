"""
Deterministic schema validator. No AI involved here.
Validates a payload against a JSON schema definition.

Schema format:
{
  "field_name": {
    "type": "string" | "integer" | "float" | "boolean" | "list" | "dict",
    "required": true | false
  },
  ...
}
"""

TYPE_MAP = {
    "string": str,
    "integer": int,
    "float": (float, int),
    "boolean": bool,
    "list": list,
    "dict": dict,
}


def validate_payload(payload: dict, schema: dict) -> list[str]:
    """
    Validate payload against schema.
    Returns a list of error strings. Empty list means valid.
    """
    errors = []

    if not isinstance(payload, dict):
        return ["Payload must be a JSON object."]

    for field, rules in schema.items():
        required = rules.get("required", True)
        expected_type = rules.get("type")

        if field not in payload:
            if required:
                errors.append(f"Missing required field: '{field}'.")
            continue

        value = payload[field]

        if expected_type and expected_type in TYPE_MAP:
            expected = TYPE_MAP[expected_type]
            # Special case: booleans are subclass of int in Python
            if expected_type == "integer" and isinstance(value, bool):
                errors.append(f"Field '{field}' must be of type integer, got boolean.")
                continue
            if not isinstance(value, expected):
                errors.append(
                    f"Field '{field}' must be of type {expected_type}, "
                    f"got {type(value).__name__}."
                )

    return errors
