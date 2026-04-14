"""
AI routes — expose AI capabilities to the frontend.
All AI output is validated before being returned.
"""

from flask import Blueprint, request, jsonify
from services.ai_service import generate_schema, explain_error

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai/generate-schema", methods=["POST"])
def ai_generate_schema():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "description is required."}), 400

    schema = generate_schema(description)
    # If AI returned an error key, surface it
    if "error" in schema:
        return jsonify({"error": schema["error"]}), 503

    return jsonify({"schema": schema}), 200


@ai_bp.route("/ai/explain-error", methods=["POST"])
def ai_explain_error():
    data = request.get_json(silent=True) or {}
    error_message = data.get("error_message", "").strip()
    if not error_message:
        return jsonify({"error": "error_message is required."}), 400

    explanation = explain_error(error_message)
    return jsonify({"explanation": explanation}), 200
