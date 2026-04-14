"""
Contract Middleware — the enforcement layer.

Runs before every request and after every response.
Validates payloads against stored contracts.
Logs all failures to the database.

AI is NOT used here. Validation is deterministic only.
"""

import json
from flask import request, g, jsonify, current_app
from services.contract_service import get_contract
from services.log_service import log_validation_failure
from validators.schema_validator import validate_payload

# Routes that are part of the guardian system itself — skip contract enforcement
INTERNAL_PREFIXES = ("/contracts", "/logs", "/ai", "/test", "/health")


def _is_internal_route(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in INTERNAL_PREFIXES)


def validate_request():
    """
    before_request hook.
    Looks up the contract for this endpoint+method and validates the request body.
    Rejects with 400 if validation fails.
    """
    if _is_internal_route(request.path):
        return None

    if request.method in ("GET", "DELETE", "HEAD", "OPTIONS"):
        return None

    contract = get_contract(request.path, request.method)
    if contract is None:
        return None

    try:
        payload = request.get_json(force=True, silent=True) or {}
    except Exception:
        payload = {}

    errors = validate_payload(payload, contract.request_schema)
    if errors:
        error_msg = "; ".join(errors)
        log_validation_failure(request.path, error_msg, "request", method=request.method)
        # Mark request as rejected so after_request skips response validation
        g.request_rejected = True
        return jsonify({
            "status": "error",
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request validation failed.",
                "details": errors,
            }
        }), 400

    g.validated_payload = payload
    return None


def validate_response_contract(response):
    """
    after_request hook.
    Validates the response body against the registered contract's response_schema.

    Rules:
    - Skip if request was already rejected (avoid double-firing)
    - Skip if route is internal
    - Skip if response is not JSON
    - Skip if no contract is registered for this endpoint
    - Warn and log if contract has no response_schema
    - Reject with 500 if response fails schema validation
    """
    if _is_internal_route(request.path):
        return response

    # Skip if request was already rejected upstream
    if g.get("request_rejected"):
        return response

    # Only validate JSON responses
    if not response.content_type or "application/json" not in response.content_type:
        return response

    contract = get_contract(request.path, request.method)
    if contract is None:
        return response

    # Warn if response_schema is missing or empty
    if not contract.response_schema:
        warning = f"Response schema missing for endpoint {request.path} [{request.method}]"
        current_app.logger.warning(warning)
        log_validation_failure(request.path, warning, "response", method=request.method)
        return response

    # Safely extract response JSON
    try:
        data = response.get_json(silent=True)
    except Exception:
        data = None

    if data is None:
        warning = f"Response body is not valid JSON for endpoint {request.path}"
        current_app.logger.warning(warning)
        log_validation_failure(request.path, warning, "response", method=request.method)
        return response

    errors = validate_payload(data, contract.response_schema)
    if errors:
        error_msg = "; ".join(errors)
        log_validation_failure(request.path, error_msg, "response", method=request.method)
        current_app.logger.error(f"Response validation failed [{request.path}]: {error_msg}")
        error_response = jsonify({
            "status": "error",
            "error": {
                "code": "INVALID_RESPONSE",
                "message": "Response does not match contract.",
                "details": errors,
            }
        })
        error_response.status_code = 500
        return error_response

    return response
