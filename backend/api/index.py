import sys
import os

# Make backend/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from app import create_app

app = create_app()

# Vercel calls this as a WSGI app
