#!/usr/bin/env python3
"""
Test version of Google Maps Scraper to verify setup
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import sys
import os

def test_imports():
    """Test if all required modules are available"""
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Playwright import failed: {e}")
        return False

def test_chrome_path():
    """Test if Chrome executable exists"""
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome_path):
        print(f"✅ Chrome found at: {chrome_path}")
        return True
    else:
        print(f"❌ Chrome not found at: {chrome_path}")
        return False

async def test_playwright_browser():
    """Test if Playwright can launch a browser"""
    try:
        from playwright.async_api import async_playwright
        
        print("Testing Playwright browser launch...")
        playwright = await async_playwright().start()
        
        # Try to launch chromium
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        title = await page.title()
        print(f"✅ Successfully loaded Google: {title}")
        
        await browser.close()
        await playwright.stop()
        return True
        
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

class TestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Google Maps Scraper - Test")
        self.root.geometry("600x400")
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Google Maps Scraper - Test", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Test results area
        self.results_text = tk.Text(main_frame, height=15, width=70)
        self.results_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        test_button = ttk.Button(button_frame, text="Run Tests", command=self.run_tests)
        test_button.pack(side=tk.LEFT, padx=5)
        
        launch_button = ttk.Button(button_frame, text="Launch Full Scraper", 
                                  command=self.launch_full_scraper)
        launch_button.pack(side=tk.LEFT, padx=5)
        
        close_button = ttk.Button(button_frame, text="Close", command=self.root.quit)
        close_button.pack(side=tk.LEFT, padx=5)
        
    def log_result(self, message):
        """Add message to results text"""
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
        
    def run_tests(self):
        """Run all tests"""
        self.results_text.delete(1.0, tk.END)
        self.log_result("🧪 Running Google Maps Scraper Tests...\n")
        
        # Test 1: Check imports
        self.log_result("Test 1: Checking imports...")
        if test_imports():
            self.log_result("✅ All imports successful\n")
        else:
            self.log_result("❌ Import test failed\n")
            return
        
        # Test 2: Check Chrome
        self.log_result("Test 2: Checking Chrome installation...")
        if test_chrome_path():
            self.log_result("✅ Chrome found\n")
        else:
            self.log_result("❌ Chrome test failed\n")
            return
        
        # Test 3: Async browser test
        self.log_result("Test 3: Testing Playwright browser...")
        try:
            result = asyncio.run(test_playwright_browser())
            if result:
                self.log_result("✅ Playwright browser test successful\n")
            else:
                self.log_result("❌ Playwright browser test failed\n")
                return
        except Exception as e:
            self.log_result(f"❌ Async test failed: {e}\n")
            return
        
        self.log_result("🎉 ALL TESTS PASSED!")
        self.log_result("Your system is ready to run the Google Maps Scraper!")
        
    def launch_full_scraper(self):
        """Launch the full scraper application"""
        try:
            import subprocess
            subprocess.Popen([sys.executable, "google_maps_scraper_dark.py"], 
                           env=dict(os.environ, TK_SILENCE_DEPRECATION="1"))
            self.log_result("✅ Full scraper launched!")
        except Exception as e:
            self.log_result(f"❌ Failed to launch full scraper: {e}")
        
    def run(self):
        self.root.mainloop()

def main():
    """Main entry point"""
    print("Google Maps Scraper - Test Mode")
    app = TestGUI()
    app.run()

if __name__ == "__main__":
    main()
