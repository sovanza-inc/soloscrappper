#!/usr/bin/env python3
"""
Setup script for Solo Scrapper
Installs required dependencies and Playwright browsers
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print("✅ SUCCESS!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("Solo Scrapper - Setup Script")
    print("="*50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Install pip dependencies
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                      "Installing Python dependencies"):
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Install Playwright browsers
    if not run_command("playwright install", "Installing Playwright browsers"):
        print("❌ Failed to install Playwright browsers")
        print("Please try running manually: playwright install")
        sys.exit(1)
    
    # Install Playwright system dependencies (Linux only)
    if sys.platform.startswith('linux'):
        run_command("playwright install-deps", "Installing system dependencies (Linux)")
    
    print("\n" + "="*50)
    print("✅ Setup completed successfully!")
    print("="*50)
    print("\nYou can now run the scraper with:")
    print("python google_maps_scraper_pro.py (PyQt5 version - recommended)")
    print("\nOr create an executable with:")
    print("pyinstaller --onefile --noconsole google_maps_scraper_pro.py")

if __name__ == "__main__":
    main()
