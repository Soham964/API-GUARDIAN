#!/bin/bash
# Run this on EC2 to pull latest changes and restart
# Usage: bash deploy/update.sh

set -e
cd /home/ubuntu/app

echo "=== Pulling latest code ==="
git pull

echo "=== Updating Python deps ==="
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo "=== Rebuilding frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Restarting backend ==="
sudo systemctl restart api-guardian

echo "=== Done! ==="
