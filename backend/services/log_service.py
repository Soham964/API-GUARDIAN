import sys
from db import db
from models.log import ValidationLog, VALID_DIRECTIONS


def log_validation_failure(endpoint: str, error_message: str, direction: str, method: str = "UNKNOWN"):
    """
    Persist a validation failure to the database.

    direction must be explicitly "request" or "response" — never assumed.
    """
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"Invalid log direction: {repr(direction)}. Must be 'request' or 'response'.")

    print(f"[LOG] {direction.upper()} error at {method} {endpoint}: {error_message[:80]}", file=sys.stderr)

    entry = ValidationLog(
        endpoint=endpoint,
        method=method.upper(),
        error_message=error_message,
        direction=direction,
    )
    db.session.add(entry)
    db.session.commit()


def get_all_logs() -> list[dict]:
    logs = ValidationLog.query.order_by(ValidationLog.timestamp.desc()).all()
    return [log.to_dict() for log in logs]
