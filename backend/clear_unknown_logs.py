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
        result = conn.execute(text("DELETE FROM logs WHERE method = 'UNKNOWN'"))
        conn.commit()
        print(f"Deleted {result.rowcount} stale log(s) with UNKNOWN method.")
    from models.log import ValidationLog
    print(f"Remaining logs: {ValidationLog.query.count()}")
