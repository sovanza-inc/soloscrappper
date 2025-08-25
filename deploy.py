#!/usr/bin/env python3
"""
Deployment script for the Stripe Webhook API
This script helps deploy the API to production
"""

import os
import sys
import subprocess
from pathlib import Path

def check_production_env():
    """Check if production environment is properly configured"""
    print("🔍 Checking production environment...")
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'PRODUCT_ID',
        'PRICE_ID',
        'WEBHOOK_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these variables in your production environment")
        return False
    
    print("✅ Production environment configured")
    return True

def install_production_dependencies():
    """Install production dependencies"""
    print("📦 Installing production dependencies...")
    
    try:
        # Install production requirements
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            'flask', 'stripe', 'python-dotenv', 'gunicorn'
        ])
        print("✅ Production dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install production dependencies")
        return False

def create_gunicorn_config():
    """Create gunicorn configuration file"""
    print("📝 Creating gunicorn configuration...")
    
    gunicorn_config = """
# Gunicorn configuration for Stripe Webhook API
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
"""
    
    try:
        with open('gunicorn.conf.py', 'w') as f:
            f.write(gunicorn_config)
        print("✅ Gunicorn configuration created")
        return True
    except Exception as e:
        print(f"❌ Failed to create gunicorn config: {e}")
        return False

def create_systemd_service():
    """Create systemd service file"""
    print("📝 Creating systemd service...")
    
    service_content = """[Unit]
Description=Stripe Webhook API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory={}
Environment=PATH={}/bin
ExecStart={}/bin/gunicorn --config gunicorn.conf.py stripe_webhook_api:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
""".format(
        os.getcwd(),
        os.getcwd(),
        os.getcwd()
    )
    
    try:
        with open('stripe-webhook-api.service', 'w') as f:
            f.write(service_content)
        print("✅ Systemd service file created")
        print("💡 To install the service:")
        print("   sudo cp stripe-webhook-api.service /etc/systemd/system/")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl enable stripe-webhook-api")
        print("   sudo systemctl start stripe-webhook-api")
        return True
    except Exception as e:
        print(f"❌ Failed to create systemd service: {e}")
        return False

def create_nginx_config():
    """Create nginx configuration"""
    print("📝 Creating nginx configuration...")
    
    nginx_config = """server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
"""
    
    try:
        with open('nginx-stripe-webhook.conf', 'w') as f:
            f.write(nginx_config)
        print("✅ Nginx configuration created")
        print("💡 To use this configuration:")
        print("   sudo cp nginx-stripe-webhook.conf /etc/nginx/sites-available/")
        print("   sudo ln -s /etc/nginx/sites-available/nginx-stripe-webhook.conf /etc/nginx/sites-enabled/")
        print("   sudo nginx -t")
        print("   sudo systemctl reload nginx")
        return True
    except Exception as e:
        print(f"❌ Failed to create nginx config: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Stripe Webhook API Production Deployment")
    print("="*60)
    
    # Check environment
    if not check_production_env():
        sys.exit(1)
    
    # Install dependencies
    if not install_production_dependencies():
        sys.exit(1)
    
    # Create configuration files
    create_gunicorn_config()
    create_systemd_service()
    create_nginx_config()
    
    print("\n✅ Deployment setup complete!")
    print("\n📋 Next steps:")
    print("   1. Update nginx configuration with your domain")
    print("   2. Install and start the systemd service")
    print("   3. Configure nginx and reload")
    print("   4. Update Stripe webhook URL to your production domain")
    print("   5. Test the webhook endpoint")
    
    print("\n🔒 Security reminders:")
    print("   - Use HTTPS in production")
    print("   - Set up SSL certificates (Let's Encrypt)")
    print("   - Configure firewall rules")
    print("   - Monitor logs and access")

if __name__ == "__main__":
    main()
