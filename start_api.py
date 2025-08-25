#!/usr/bin/env python3
"""
Quick start script for the Stripe Webhook API
This script helps set up the environment and start the API
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'stripe', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}: Installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: Not installed")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run manually:")
            print(f"   pip install {' '.join(missing_packages)}")
            return False
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path('.env')
    template_file = Path('env_template.txt')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if template_file.exists():
        print("📝 Creating .env file from template...")
        try:
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(template_content)
            
            print("✅ .env file created successfully")
            print("💡 Please review and update the values in .env file if needed")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("⚠️  No env_template.txt found. Please create .env file manually")
        return False

def start_api():
    """Start the Flask API"""
    print("\n🚀 Starting Stripe Webhook API...")
    print("="*60)
    
    try:
        # Import and run the API
        from stripe_webhook_api import app
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000
        )
    except KeyboardInterrupt:
        print("\n\n👋 API stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start API: {e}")
        print("💡 Make sure all dependencies are installed and configuration is correct")

def main():
    """Main function"""
    print("🎯 Stripe Webhook API Quick Start")
    print("="*60)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again")
        sys.exit(1)
    
    # Setup environment
    if not create_env_file():
        print("\n⚠️  Environment setup incomplete, but continuing...")
    
    print("\n✅ All checks passed!")
    print("\n📋 Configuration:")
    print("   - Product ID: prod_SvXJsNpsCxwnls")
    print("   - Price ID: price_1RzgEeFaG3nZ4nVpjiSCwpdA")
    print("   - Payment Link: https://buy.stripe.com/test_3cI4gzgoe5Nu6qz14je3e00")
    print("   - Webhook URL: https://c5afae26e8d9.ngrok-free.app/api/webhook")
    
    print("\n💡 Tips:")
    print("   - Use Ctrl+C to stop the API")
    print("   - Check the terminal for webhook events")
    print("   - Use ngrok to test webhooks locally")
    
    # Start the API
    start_api()

if __name__ == "__main__":
    main()
