import sys
import os

# Make backend/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env for local dev — on Vercel, env vars come from the dashboard
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
except Exception:
    pass

from app import create_app
from db import db

app = create_app()

# Ensure tables exist on cold start
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    import logging
    logging.warning(f"db.create_all() failed: {e}")
