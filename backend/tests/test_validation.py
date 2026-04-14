"""
Tests for the core validation system.
Covers: valid request, missing field, wrong type, invalid response,
        missing response schema, middleware enforcement, logging.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from db import db as _db
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    GROQ_API_KEY = ""


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_contract(client):
    """Register a contract for /api/users POST."""
    resp = client.post("/contracts", json={
        "endpoint": "/api/users",
        "method": "POST",
        "request_schema": {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True},
            "email": {"type": "string", "required": False},
        },
        "response_schema": {
            "id": {"type": "integer", "required": True},
            "name": {"type": "string", "required": True},
        },
    })
    assert resp.status_code == 201
    return resp.get_json()


# ── Contract CRUD ──────────────────────────────────────────────────────────────

class TestContractManagement:
    def test_create_contract(self, client):
        resp = client.post("/contracts", json={
            "endpoint": "/api/items",
            "method": "GET",
            "request_schema": {},
            "response_schema": {"items": {"type": "list", "required": True}},
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["endpoint"] == "/api/items"
        assert data["method"] == "GET"

    def test_create_contract_missing_fields(self, client):
        resp = client.post("/contracts", json={"endpoint": "/api/x"})
        assert resp.status_code == 400
        assert "Missing fields" in resp.get_json()["error"]

    def test_create_contract_empty_response_schema_rejected(self, client):
        """response_schema must not be empty."""
        resp = client.post("/contracts", json={
            "endpoint": "/api/test",
            "method": "POST",
            "request_schema": {"name": {"type": "string", "required": True}},
            "response_schema": {},  # empty — should be rejected
        })
        assert resp.status_code == 400
        assert "response_schema" in resp.get_json()["error"]

    def test_create_contract_invalid_schema_type(self, client):
        resp = client.post("/contracts", json={
            "endpoint": "/api/test",
            "method": "POST",
            "request_schema": "not a dict",
            "response_schema": {"id": {"type": "integer", "required": True}},
        })
        assert resp.status_code == 400

    def test_list_contracts(self, client, sample_contract):
        resp = client.get("/contracts")
        assert resp.status_code == 200
        contracts = resp.get_json()
        assert any(c["endpoint"] == "/api/users" for c in contracts)

    def test_delete_contract(self, client, sample_contract):
        contract_id = sample_contract["id"]
        resp = client.delete(f"/contracts/{contract_id}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Contract deleted."

    def test_delete_nonexistent_contract(self, client):
        resp = client.delete("/contracts/9999")
        assert resp.status_code == 404


# ── Schema Validator Unit Tests ────────────────────────────────────────────────

class TestSchemaValidator:
    def setup_method(self):
        from validators.schema_validator import validate_payload
        self.validate = validate_payload

    def test_valid_payload(self):
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True},
        }
        errors = self.validate({"name": "Alice", "age": 30}, schema)
        assert errors == []

    def test_missing_required_field(self):
        schema = {"name": {"type": "string", "required": True}}
        errors = self.validate({}, schema)
        assert any("name" in e for e in errors)

    def test_optional_field_absent_is_ok(self):
        schema = {"email": {"type": "string", "required": False}}
        errors = self.validate({}, schema)
        assert errors == []

    def test_wrong_type_string_for_integer(self):
        schema = {"age": {"type": "integer", "required": True}}
        errors = self.validate({"age": "thirty"}, schema)
        assert any("age" in e for e in errors)

    def test_boolean_rejected_as_integer(self):
        schema = {"count": {"type": "integer", "required": True}}
        errors = self.validate({"count": True}, schema)
        assert any("count" in e for e in errors)

    def test_non_dict_payload(self):
        schema = {"name": {"type": "string", "required": True}}
        errors = self.validate("not a dict", schema)
        assert len(errors) > 0

    def test_float_accepts_int(self):
        schema = {"score": {"type": "float", "required": True}}
        errors = self.validate({"score": 5}, schema)
        assert errors == []

    def test_multiple_errors(self):
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True},
        }
        errors = self.validate({"name": 123, "age": "old"}, schema)
        assert len(errors) == 2


# ── Test Endpoint (validate via API) ──────────────────────────────────────────

class TestValidateEndpoint:
    def test_valid_request_payload(self, client, sample_contract):
        resp = client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"name": "Bob", "age": 25},
            "direction": "request",
        })
        assert resp.status_code == 200
        assert resp.get_json()["valid"] is True

    def test_invalid_request_missing_field(self, client, sample_contract):
        resp = client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"name": "Bob"},  # missing age
            "direction": "request",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["valid"] is False
        assert any("age" in e for e in data["errors"])

    def test_invalid_request_wrong_type(self, client, sample_contract):
        resp = client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"name": "Bob", "age": "not-a-number"},
            "direction": "request",
        })
        assert resp.status_code == 200
        assert resp.get_json()["valid"] is False

    def test_valid_response_payload(self, client, sample_contract):
        """Valid response matches schema — should pass."""
        resp = client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"id": 1, "name": "Bob"},
            "direction": "response",
        })
        assert resp.status_code == 200
        assert resp.get_json()["valid"] is True

    def test_invalid_response_missing_field(self, client, sample_contract):
        """Response missing required 'id' field — should fail."""
        resp = client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"name": "Bob"},  # missing id
            "direction": "response",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["valid"] is False
        assert any("id" in e for e in data["errors"])

    def test_invalid_response_wrong_type(self, client, sample_contract):
        """Response with wrong type for 'id' — should fail."""
        resp = client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"id": "not-an-int", "name": "Bob"},
            "direction": "response",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["valid"] is False
        assert any("id" in e for e in data["errors"])

    def test_no_contract_returns_404(self, client):
        resp = client.post("/test/validate", json={
            "endpoint": "/nonexistent",
            "method": "POST",
            "payload": {},
        })
        assert resp.status_code == 404

    def test_missing_endpoint_param(self, client):
        resp = client.post("/test/validate", json={"payload": {}})
        assert resp.status_code == 400


# ── Middleware Integration ─────────────────────────────────────────────────────

@pytest.fixture
def middleware_app():
    """App with routes pre-registered for middleware tests (Flask 3 requirement)."""
    from flask import jsonify as _jsonify

    app = create_app(TestConfig)

    @app.route("/api/users", methods=["POST"])
    def fake_users_valid():
        # Returns a valid response matching the contract
        return _jsonify({"id": 1, "name": "Alice"}), 200

    @app.route("/api/users/bad", methods=["POST"])
    def fake_users_bad_response():
        # Returns an INVALID response (missing required fields)
        return _jsonify({"message": "created"}), 200

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def mw_client(middleware_app):
    return middleware_app.test_client()


@pytest.fixture
def mw_contract(mw_client):
    resp = mw_client.post("/contracts", json={
        "endpoint": "/api/users",
        "method": "POST",
        "request_schema": {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True},
        },
        "response_schema": {
            "id": {"type": "integer", "required": True},
            "name": {"type": "string", "required": True},
        },
    })
    assert resp.status_code == 201
    # Register same contract for /api/users/bad
    mw_client.post("/contracts", json={
        "endpoint": "/api/users/bad",
        "method": "POST",
        "request_schema": {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True},
        },
        "response_schema": {
            "id": {"type": "integer", "required": True},
            "name": {"type": "string", "required": True},
        },
    })
    return resp.get_json()


class TestMiddleware:
    def test_middleware_rejects_invalid_request(self, mw_client, mw_contract):
        """Middleware blocks a request missing a required field."""
        resp = mw_client.post("/api/users", json={"name": "Alice"})  # missing age
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "INVALID_REQUEST"

    def test_middleware_passes_valid_request(self, mw_client, mw_contract):
        """Middleware allows a fully valid request through."""
        resp = mw_client.post("/api/users", json={"name": "Alice", "age": 30})
        assert resp.status_code == 200

    def test_middleware_rejects_invalid_response(self, mw_client, mw_contract):
        """Middleware catches a response that doesn't match the response schema."""
        resp = mw_client.post("/api/users/bad", json={"name": "Alice", "age": 30})
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "INVALID_RESPONSE"
        assert len(data["error"]["details"]) > 0

    def test_middleware_valid_response_passes(self, mw_client, mw_contract):
        """Valid response passes response validation."""
        resp = mw_client.post("/api/users", json={"name": "Alice", "age": 30})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == 1
        assert data["name"] == "Alice"


# ── Missing Response Schema Warning ───────────────────────────────────────────

class TestMissingResponseSchema:
    def test_empty_response_schema_rejected_at_creation(self, client):
        """Cannot create a contract with an empty response_schema."""
        resp = client.post("/contracts", json={
            "endpoint": "/api/ping",
            "method": "POST",
            "request_schema": {},
            "response_schema": {},
        })
        assert resp.status_code == 400
        assert "response_schema" in resp.get_json()["error"]

    def test_warning_logged_for_missing_schema(self, middleware_app, mw_client):
        """
        If a contract somehow has an empty response_schema,
        a warning is logged and the response is passed through.
        """
        from models.contract import Contract
        from db import db

        # Directly insert a contract with empty response_schema (bypassing route validation)
        with middleware_app.app_context():
            c = Contract(
                endpoint="/api/legacy",
                method="POST",
                request_schema={},
                response_schema={},  # empty — simulates legacy/corrupt data
            )
            db.session.add(c)
            db.session.commit()

        @middleware_app.route("/api/legacy", methods=["POST"])
        def legacy():
            from flask import jsonify as j
            return j({"anything": "goes"}), 200

        resp = mw_client.post("/api/legacy", json={})
        # Should pass through (not crash), warning is logged
        assert resp.status_code == 200

        # Warning should be in logs DB
        logs_resp = mw_client.get("/logs")
        logs = logs_resp.get_json()
        assert any("legacy" in log["endpoint"] for log in logs)


# ── Logs ──────────────────────────────────────────────────────────────────────

class TestLogs:
    def test_logs_recorded_on_request_failure(self, client, sample_contract):
        client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {},
            "direction": "request",
        })
        resp = client.get("/logs")
        assert resp.status_code == 200
        logs = resp.get_json()
        assert any("/api/users" in log["endpoint"] for log in logs)

    def test_logs_recorded_on_response_failure(self, client, sample_contract):
        client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"name": "Bob"},  # missing id — invalid response
            "direction": "response",
        })
        resp = client.get("/logs")
        logs = resp.get_json()
        assert any(
            log["direction"] == "response" and "/api/users" in log["endpoint"]
            for log in logs
        )

    def test_log_structure(self, client, sample_contract):
        """Each log entry has required fields."""
        client.post("/test/validate", json={
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {},
            "direction": "request",
        })
        logs = client.get("/logs").get_json()
        log = logs[0]
        assert "id" in log
        assert "endpoint" in log
        assert "error_message" in log
        assert "direction" in log
        assert "timestamp" in log
