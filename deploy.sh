#!/bin/bash

# AWS EC2 Deployment Script for Homemade Pickles & Snacks

echo "Starting deployment..."

# Update system packages
sudo yum update -y

# Install Python 3 and pip
sudo yum install -y python3 python3-pip git nginx

# Clone repository (replace with your GitHub repo URL)
# git clone https://github.com/yourusername/homemade-pickles.git
# cd homemade-pickles

# Install Python dependencies
pip3 install -r requirements.txt

# Create systemd service file
sudo tee /etc/systemd/system/pickles-app.service > /dev/null <<EOF
[Unit]
Description=Homemade Pickles Flask App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/homemade-pickles
Environment=PATH=/home/ec2-user/.local/bin
ExecStart=/usr/bin/python3 home/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
sudo tee /etc/nginx/conf.d/pickles.conf > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/ec2-user/homemade-pickles/home/static;
        expires 30d;
    }
}
EOF

# Start and enable services
sudo systemctl daemon-reload
sudo systemctl enable pickles-app
sudo systemctl start pickles-app
sudo systemctl enable nginx
sudo systemctl start nginx

# Open firewall ports
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

echo "Deployment completed!"
echo "Configure your .env file with AWS credentials before starting the application."