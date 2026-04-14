"""One-time migration: add method column to logs table."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

from app import create_app
from db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(logs)"))
        columns = [row[1] for row in result]
        if "method" not in columns:
            conn.execute(text('ALTER TABLE logs ADD COLUMN method VARCHAR(10) NOT NULL DEFAULT "UNKNOWN"'))
            conn.commit()
            print("Added 'method' column to logs table.")
        else:
            print("'method' column already exists — skipping.")
    db.create_all()
    print("Done.")
