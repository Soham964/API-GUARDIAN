"""
Test endpoint — allows sending a payload and seeing validation results
without needing a real downstream service.
"""

from flask import Blueprint, request, jsonify
from services.contract_service import get_contract
from services.log_service import log_validation_failure
from validators.schema_validator import validate_payload

test_bp = Blueprint("test", __name__)


@test_bp.route("/test/validate", methods=["POST"])
def test_validate():
    data = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint")
    method = data.get("method", "POST")
    payload = data.get("payload", {})
    direction = data.get("direction", "request")  # "request" or "response"

    if not endpoint:
        return jsonify({"error": "endpoint is required."}), 400

    contract = get_contract(endpoint, method)
    if not contract:
        return jsonify({"error": f"No contract found for {method} {endpoint}"}), 404

    schema = contract.request_schema if direction == "request" else contract.response_schema
    errors = validate_payload(payload, schema)

    if errors:
        error_msg = "; ".join(errors)
        log_validation_failure(endpoint, error_msg, direction, method=method)
        return jsonify({"valid": False, "errors": errors}), 200

    return jsonify({"valid": True, "errors": []}), 200
