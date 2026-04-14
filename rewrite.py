import sys

msg = sys.stdin.read().strip()

mapping = {
    "Initial commit": "feat: init — full-stack API Contract Guardian (Flask + React + Groq AI)",
    "Add gunicorn and Procfile for Render deployment": "feat: deploy — add Procfile and gunicorn for production server",
    "feat: Supabase PostgreSQL, vercel.json, updated gitignore and requirements": "feat: db — migrate from SQLite to Supabase PostgreSQL",
    "feat: add vercel.json, serverless entry point, root requirements.txt": "feat: deploy — add Vercel serverless entry point and root requirements",
    "fix: update vercel.json to experimentalServices format": "fix: vercel — switch vercel.json to experimentalServices schema",
    "fix: add framework and entrypoint to experimentalServices": "fix: vercel — add framework and entrypoint to resolve build error",
}

print(mapping.get(msg, msg))
