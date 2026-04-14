import sys
import os

# Ensure backend/ is on the path so imports work from any working directory
sys.path.insert(0, os.path.dirname(__file__))

# Load .env BEFORE config is imported so os.environ is populated in time
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
except ImportError:
    pass

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from db import init_db
from models import Contract, ValidationLog  # noqa: F401 — needed for migrations
from routes.contract_routes import contract_bp
from routes.test_routes import test_bp
from routes.ai_routes import ai_bp
from middleware.contract_middleware import validate_request, validate_response_contract


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/*": {"origins": "*"}})
    init_db(app)

    # Register blueprints
    app.register_blueprint(contract_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(ai_bp)

    # Register middleware
    app.before_request(validate_request)
    app.after_request(validate_response_contract)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        from db import db
        db.create_all()
    app.run(debug=True, port=5000)
