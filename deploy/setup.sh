#!/bin/bash
# EC2 setup script — run once on a fresh Ubuntu 22.04 t2.micro instance
# Usage: bash setup.sh

set -e

echo "=== Updating system ==="
sudo apt-get update -y
sudo apt-get upgrade -y

echo "=== Installing dependencies ==="
sudo apt-get install -y python3 python3-pip python3-venv nginx git curl

echo "=== Installing Node.js 20 ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "=== Cloning repo ==="
cd /home/ubuntu
git clone https://github.com/Soham964/API-GUARDIAN.git app
cd app

echo "=== Setting up Python venv ==="
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo "=== Building frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Creating .env file ==="
cat > backend/.env << 'EOF'
DATABASE_URL=sqlite:///api_guardian.db
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=change-this-in-production
EOF
echo ">>> Edit backend/.env with your real values before starting the app <<<"

echo "=== Setting up systemd service ==="
sudo cp deploy/api-guardian.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable api-guardian
sudo systemctl start api-guardian

echo "=== Setting up nginx ==="
sudo cp deploy/nginx.conf /etc/nginx/sites-available/api-guardian
sudo ln -sf /etc/nginx/sites-available/api-guardian /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== Done! ==="
echo "App is running. Visit http://$(curl -s ifconfig.me)"
