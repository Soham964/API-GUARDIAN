from flask import Blueprint, request, jsonify
from services.contract_service import (
    create_contract,
    get_all_contracts,
    delete_contract,
)
from services.log_service import get_all_logs

contract_bp = Blueprint("contracts", __name__)


@contract_bp.route("/contracts", methods=["GET"])
def list_contracts():
    return jsonify(get_all_contracts()), 200


@contract_bp.route("/contracts", methods=["POST"])
def add_contract():
    data = request.get_json(silent=True) or {}
    required = ["endpoint", "method", "request_schema", "response_schema"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not isinstance(data["request_schema"], dict):
        return jsonify({"error": "request_schema must be a JSON object."}), 400
    if not isinstance(data["response_schema"], dict):
        return jsonify({"error": "response_schema must be a JSON object."}), 400
    if not data["response_schema"]:
        return jsonify({"error": "response_schema is required and cannot be empty."}), 400

    contract = create_contract(
        endpoint=data["endpoint"],
        method=data["method"],
        request_schema=data["request_schema"],
        response_schema=data["response_schema"],
    )
    return jsonify(contract), 201


@contract_bp.route("/contracts/<int:contract_id>", methods=["DELETE"])
def remove_contract(contract_id):
    if delete_contract(contract_id):
        return jsonify({"message": "Contract deleted."}), 200
    return jsonify({"error": "Contract not found."}), 404


@contract_bp.route("/logs", methods=["GET"])
def list_logs():
    return jsonify(get_all_logs()), 200
