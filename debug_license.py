#!/usr/bin/env python3

import os
import sys
import pickle
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.license import LicenseManager

def debug_license_status():
    """Debug license status and cache"""
    print("=== License Debug Information ===")
    
    # Initialize license manager
    license_manager = LicenseManager()
    
    print(f"Machine ID: {license_manager.machine_id}")
    print(f"Cache file path: {license_manager.cache_file}")
    print(f"Cache file exists: {os.path.exists(license_manager.cache_file)}")
    
    # Check cache file contents
    if os.path.exists(license_manager.cache_file):
        try:
            with open(license_manager.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            print("\n=== Cache File Contents ===")
            for key, value in cache_data.items():
                if key == 'license_key':
                    print(f"{key}: {value[:8]}...{value[-8:] if len(value) > 16 else value}")
                else:
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"Error reading cache file: {e}")
    else:
        print("No cache file found")
    
    # Test license validation methods
    print("\n=== License Validation Tests ===")
    print(f"has_valid_cached_license(): {license_manager.has_valid_cached_license()}")
    
    # Get license status
    status = license_manager.get_license_status()
    print(f"\n=== License Status ===")
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Test database connection
    print("\n=== Database Connection Test ===")
    try:
        conn = license_manager._get_connection()
        if conn:
            print("Database connection: SUCCESS")
            conn.close()
        else:
            print("Database connection: FAILED")
    except Exception as e:
        print(f"Database connection error: {e}")
    
    # Get cached license key
    cached_key = license_manager.get_cached_license_key()
    if cached_key:
        print(f"\nCached license key: {cached_key[:8]}...{cached_key[-8:]}")
        
        # Test database verification
        print("\n=== Database Verification Test ===")
        try:
            db_valid = license_manager.verify_cached_license_with_database(cached_key)
            print(f"Database verification result: {db_valid}")
        except Exception as e:
            print(f"Database verification error: {e}")
    else:
        print("\nNo cached license key found")

if __name__ == "__main__":
    debug_license_status()