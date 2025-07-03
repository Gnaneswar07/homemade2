#!/bin/bash

# EC2 Deployment Script for Homemade Pickles & Snacks
# Run this script on your EC2 instance

echo "🚀 Starting EC2 Deployment..."

# Update system
sudo yum update -y

# Install Python 3 and pip
sudo yum install -y python3 python3-pip git

# Install required system packages
sudo yum install -y gcc python3-devel

# Clone your repository (replace with your GitHub URL)
echo "📥 Cloning repository..."
# git clone https://github.com/yourusername/homemade-pickles.git
# cd homemade-pickles

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user flask boto3 python-dotenv requests

# Set environment variables
echo "🔧 Setting environment variables..."
export SECRET_KEY="pickle-secret-key-2025"
export AWS_REGION="us-east-1"
export ADMIN_EMAIL="admin@pickles.com"
export PORT="5000"
export DEBUG="False"

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/pickles-app.service > /dev/null <<EOF
[Unit]
Description=Homemade Pickles Flask App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/homemade-pickles
Environment=PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=SECRET_KEY=pickle-secret-key-2025
Environment=AWS_REGION=us-east-1
Environment=ADMIN_EMAIL=admin@pickles.com
Environment=PORT=5000
Environment=DEBUG=False
ExecStart=/usr/bin/python3 home/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Start the service
echo "🔄 Starting Flask application..."
sudo systemctl daemon-reload
sudo systemctl enable pickles-app
sudo systemctl start pickles-app

# Check service status
echo "📊 Checking service status..."
sudo systemctl status pickles-app

# Open firewall port
echo "🔥 Opening firewall port..."
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# Test the application
echo "🧪 Testing application..."
sleep 5
curl -I http://localhost:5000

echo "✅ Deployment completed!"
echo "Your app should be running on http://YOUR-EC2-IP:5000"