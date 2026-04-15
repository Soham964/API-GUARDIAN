import sys
import os

# Make backend/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from app import create_app
from db import db

app = create_app()

# Ensure tables exist (runs once per cold start on Vercel)
with app.app_context():
    db.create_all()
