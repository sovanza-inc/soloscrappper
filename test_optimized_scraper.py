#!/usr/bin/env python3
"""
Test script for the optimized Google Maps scraper
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the current directory to the path so we can import the scraper
sys.path.insert(0, '/Users/mac/Desktop/AllinOneScrapper')

from google_maps_scraper_dark import GoogleMapsScraper

async def test_scraper():
    """Test the optimized scraper"""
    print("🚀 Starting Google Maps Scraper Test")
    
    scraper = GoogleMapsScraper()
    
    # Chrome paths for macOS
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    profile_path = str(Path.home() / "Library/Application Support/Google/Chrome")
    
    try:
        # Test setup
        print("📝 Testing browser setup...")
        success = await scraper.setup_browser(chrome_path, profile_path)
        
        if not success:
            print("❌ Browser setup failed")
            return
        
        print("✅ Browser setup successful")
        
        # Test search
        print("🔍 Testing search for 'coffee shops near me'...")
        
        def progress_callback(message):
            print(f"Progress: {message}")
        
        def business_callback(business_data):
            print(f"Found: {business_data.get('name', 'Unknown')} - {business_data.get('address', 'No address')}")
        
        # Mock callback objects that have emit method
        class MockCallback:
            def __init__(self, func):
                self.func = func
                
            def emit(self, message):
                self.func(message)
        
        progress_cb = MockCallback(progress_callback)
        business_cb = business_callback
        
        results = await scraper.search_keyword(
            "coffee shops near me", 
            progress_callback=progress_cb,
            business_callback=business_cb
        )
        
        print(f"\n🎉 Test complete! Found {len(results)} businesses:")
        for i, business in enumerate(results[:5], 1):  # Show first 5
            print(f"{i}. {business.get('name', 'N/A')} - {business.get('address', 'N/A')}")
        
        if len(results) > 5:
            print(f"... and {len(results) - 5} more businesses")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    
    finally:
        # Cleanup
        await scraper.close_browser()
        print("🔧 Browser closed")

if __name__ == "__main__":
    print("🧪 Running scraper test...")
    asyncio.run(test_scraper())
