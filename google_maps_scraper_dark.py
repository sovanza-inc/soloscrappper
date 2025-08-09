#!/usr/bin/env python3
"""
Google Maps Scraper - Production Ready PyQt5 GUI Application
Scrapes Google My Business profiles using Playwright with real Chrome browser
"""

import sys
import os
import asyncio
import threading
import csv
import random
import time
from pathlib import Path
from typing import List, Dict, Optional
import subprocess

# Import PyQt5
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                                QTextEdit, QLineEdit, QFileDialog, QMessageBox,
                                QProgressBar, QGroupBox, QScrollArea, QFrame,
                                QSplitter, QTabWidget)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QIcon, QPixmap
except ImportError:
    print("PyQt5 is not installed. Please install it using:")
    print("pip install PyQt5")
    sys.exit(1)

# Import Playwright
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("Playwright is not installed. Please install it using:")
    print("pip install playwright")
    print("python -m playwright install")
    sys.exit(1)


class GoogleMapsScraper:
    """Google Maps scraper using Playwright with real Chrome browser"""
    
    def __init__(self):
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.results: List[Dict[str, str]] = []
        
    async def setup_browser(self, chrome_path: str, profile_path: str, progress_callback=None) -> bool:
        """Setup Chrome browser with persistent context"""
        try:
            if progress_callback:
                progress_callback.emit("Setting up Chrome browser...")
                
            playwright = await async_playwright().start()
            
            # Create a unique profile directory to avoid conflicts
            import tempfile
            import shutil
            from pathlib import Path
            
            # Create temporary profile directory
            temp_profile = tempfile.mkdtemp(prefix="chrome_scraper_")
            
            if progress_callback:
                progress_callback.emit(f"Using temporary profile: {temp_profile}")
            
            # Try to copy some essential data from the original profile if it exists
            original_profile = Path(profile_path)
            temp_profile_path = Path(temp_profile)
            
            # Copy login data and cookies if available (optional)
            try:
                if (original_profile / "Default" / "Login Data").exists():
                    (temp_profile_path / "Default").mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original_profile / "Default" / "Login Data", 
                               temp_profile_path / "Default" / "Login Data")
                if (original_profile / "Default" / "Cookies").exists():
                    (temp_profile_path / "Default").mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original_profile / "Default" / "Cookies", 
                               temp_profile_path / "Default" / "Cookies")
            except Exception as e:
                if progress_callback:
                    progress_callback.emit(f"Note: Could not copy profile data: {str(e)}")
            
            # Launch persistent context with temporary profile
            self.browser_context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_profile,
                executable_path=chrome_path,
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-dev-shm-usage"
                ]
            )
            
            # Create new page
            self.page = await self.browser_context.new_page()
            
            # Set realistic user agent
            await self.page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            if progress_callback:
                progress_callback.emit("Chrome browser setup complete!")
                
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"Error setting up browser: {str(e)}")
            return False
    
    async def search_keyword(self, keyword: str, progress_callback=None, business_callback=None) -> List[Dict[str, str]]:
        """ULTRA-FAST optimized search for a keyword on Google Maps"""
        if not self.page:
            return []
            
        try:
            if progress_callback:
                progress_callback.emit(f"🚀 Searching for: {keyword}")
                
            # Navigate to Google Maps with direct search URL + performance optimizations
            search_url = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}"
            
            # More reliable navigation with increased timeout
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for Google Maps to initialize
            await asyncio.sleep(3)
            
            # Try multiple selectors for the search box
            search_box_selectors = [
                'input[id="searchboxinput"]',
                'input[aria-label*="Search"]',
                'input[placeholder*="Search"]',
                '#searchboxinput',
                'input[name="q"]',
                'input[type="text"]',
                'input.tactile-searchbox-input',
                '.searchbox input'
            ]
            
            search_box = None
            
            for selector in search_box_selectors:
                try:
                    if progress_callback:
                        progress_callback.emit(f"Trying search box selector: {selector}")
                    
                    search_box = await self.page.wait_for_selector(selector, timeout=5000)
                    if search_box:
                        # Check if the element is visible and enabled
                        is_visible = await search_box.is_visible()
                        is_enabled = await search_box.is_enabled()
                        
                        if is_visible and is_enabled:
                            if progress_callback:
                                progress_callback.emit(f"✓ Found search box with: {selector}")
                            break
                        else:
                            search_box = None
                except:
                    continue
            
            if not search_box:
                if progress_callback:
                    progress_callback.emit("❌ Could not find search box")
                return []
            
            # Clear and focus on search box
            if progress_callback:
                progress_callback.emit("Focusing on search box...")
            
            await search_box.click()
            await asyncio.sleep(1)
            
            # Clear existing text
            await search_box.press('Control+a')  # Select all
            await asyncio.sleep(0.5)
            await search_box.press('Delete')     # Delete selected
            await asyncio.sleep(0.5)
            
            # Type the keyword
            if progress_callback:
                progress_callback.emit(f"Typing keyword: {keyword}")
            
            await search_box.type(keyword, delay=random.randint(100, 200))
            await asyncio.sleep(random.uniform(1, 2))
            
            # Press Enter to search
            if progress_callback:
                progress_callback.emit("Pressing Enter to search...")
            
            await search_box.press("Enter")
            
            # Wait for search to complete
            if progress_callback:
                progress_callback.emit("Waiting for search results...")
            
            await asyncio.sleep(random.uniform(3, 6))
            
            # Wait for page to stabilize
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except:
                # Continue even if networkidle times out
                pass
            
            # Wait for results to load
            try:
                await self.page.wait_for_selector('[role="main"]', timeout=15000)
            except:
                if progress_callback:
                    progress_callback.emit(f"No results found for: {keyword}")
                return []
            
            # Scroll to load all results
            await self._scroll_results_panel(progress_callback)
            
            # Extract business listings
            businesses = await self._extract_business_listings(keyword, progress_callback)
            
            return businesses
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"Error searching {keyword}: {str(e)}")
            return []
    
    async def _scroll_results_panel(self, progress_callback=None):
        """Scroll the results panel to load all businesses"""
        try:
            if progress_callback:
                progress_callback.emit("Loading all results...")
                
            # Find the scrollable results container
            results_container = await self.page.query_selector('[role="main"]')
            if not results_container:
                return
            
            last_height = 0
            scroll_attempts = 0
            max_scrolls = 20
            
            while scroll_attempts < max_scrolls:
                # Scroll down in the results panel
                await self.page.evaluate("""
                    () => {
                        const resultsPanel = document.querySelector('[role="main"]');
                        if (resultsPanel) {
                            resultsPanel.scrollTop += 1000;
                        }
                    }
                """)
                
                await asyncio.sleep(random.uniform(2, 3))
                
                # Check if new content loaded
                current_height = await self.page.evaluate("""
                    () => {
                        const resultsPanel = document.querySelector('[role="main"]');
                        return resultsPanel ? resultsPanel.scrollHeight : 0;
                    }
                """)
                
                if current_height == last_height:
                    break
                    
                last_height = current_height
                scroll_attempts += 1
                
                if progress_callback:
                    progress_callback.emit(f"Scrolling... (attempt {scroll_attempts}/{max_scrolls})")
                    
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"Error during scrolling: {str(e)}")
    
    async def _extract_business_listings(self, keyword: str, progress_callback=None) -> List[Dict[str, str]]:
        """Extract business information from all listings"""
        businesses = []
        
        try:
            # Wait for content to load completely
            await asyncio.sleep(5)
            
            if progress_callback:
                progress_callback.emit("Looking for business listings...")
            
            # More specific selectors for Google Maps business listings
            selectors_to_try = [
                # Most reliable selectors for business cards
                'div[role="article"]',
                'div[jsaction*="pane.selectResult"]',
                'a[data-cid]',
                '[data-result-index]',
                'div.Nv2PK',  # Google Maps business card class
                '.hfpxzc',   # Another common business card class
                'div[data-result-ad-index]',
                # Fallback to any clickable business elements
                'a[href*="/maps/place/"]',
                'div[jsaction*="mouseover"]'
            ]
            
            business_elements = []
            selected_selector = None
            
            for selector in selectors_to_try:
                if progress_callback:
                    progress_callback.emit(f"Trying selector: {selector}")
                
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) >= 3:  # Need at least 3 results to be valid
                    business_elements = elements
                    selected_selector = selector
                    if progress_callback:
                        progress_callback.emit(f"✓ Found {len(elements)} businesses with: {selector}")
                    break
                await asyncio.sleep(1)
            
            if not business_elements:
                if progress_callback:
                    progress_callback.emit("❌ No business listings found")
                return businesses
            
            # Process each business element
            processed_count = 0
            for i, element in enumerate(business_elements[:100]):  # Process up to 100 results
                try:
                    if progress_callback:
                        progress_callback.emit(f"Processing business {i+1}/{min(len(business_elements), 100)}")
                    
                    # Scroll element into view
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    
                    # Click on the business element
                    await element.click(force=True)
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Extract business details from the side panel
                    business_data = await self._extract_business_details(keyword, progress_callback)
                    
                    if business_data and business_data.get('name') and business_data.get('name') != 'Results':
                        businesses.append(business_data)
                        processed_count += 1
                        if progress_callback:
                            progress_callback.emit(f"✓ Extracted: {business_data.get('name', 'Unknown')} ({processed_count} total)")
                    else:
                        if progress_callback:
                            progress_callback.emit(f"⚠ Skipped invalid business data")
                    
                    # Small delay between businesses
                    await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    if progress_callback:
                        progress_callback.emit(f"Error processing business {i+1}: {str(e)}")
                    continue
            
            if progress_callback:
                progress_callback.emit(f"Successfully extracted {processed_count} businesses")
                    
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"Error extracting listings: {str(e)}")
        
        return businesses
    
    async def _extract_business_details(self, keyword: str, progress_callback=None) -> Dict[str, str]:
        """Extract details from a single business profile"""
        business_data = {
            'keyword': keyword,
            'name': '',
            'address': '',
            'phone': '',
            'website': '',
            'rating': '',
            'reviews': '',
            'category': ''
        }
        
        try:
            # Wait for the business panel to load completely
            await asyncio.sleep(4)
            
            if progress_callback:
                progress_callback.emit("Extracting business details...")
            
            # Extract business name with comprehensive selectors
            name_selectors = [
                'h1[data-attrid="title"]',
                'h1.DUwDvf',
                'h1.x3AX1-LfntMc-header-title-title',
                'h1.SPZz6b',
                'h1.qrShPb',
                'h1[class*="title"]',
                'div[role="main"] h1',
                '.x3AX1-LfntMc-header-title-title',
                'div[data-attrid="title"] h1',
                'h1'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = await self.page.wait_for_selector(selector, timeout=2000)
                    if name_element:
                        name_text = await name_element.inner_text()
                        if name_text and name_text.strip() and name_text.strip() != 'Results':
                            business_data['name'] = name_text.strip()
                            break
                except:
                    continue
            
            # Extract address with multiple strategies
            address_selectors = [
                '[data-item-id="address"] .Io6YTe',
                '[data-item-id="address"]',
                'div[data-attrid="address"] .Io6YTe',
                'div[data-attrid="address"]',
                'button[data-value="Directions"] .Io6YTe',
                'button[data-value="Directions"]',
                '.Io6YTe[data-attrid="address"]',
                'div.rogA2c .Io6YTe',
                'div[jsaction*="address"] .Io6YTe'
            ]
            
            for selector in address_selectors:
                try:
                    address_element = await self.page.query_selector(selector)
                    if address_element:
                        address_text = await address_element.inner_text()
                        if address_text and address_text.strip():
                            business_data['address'] = address_text.strip()
                            break
                except:
                    continue
            
            # Extract phone number with comprehensive selectors
            phone_selectors = [
                '[data-item-id="phone:tel:"] .Io6YTe',
                '[data-item-id*="phone"] .Io6YTe', 
                '[data-item-id*="phone"]',
                'div[data-attrid="phone"] .Io6YTe',
                'div[data-attrid="phone"]',
                'button[data-value*="phone"] .Io6YTe',
                'button[data-value*="phone"]',
                'a[href^="tel:"]',
                'div[jsaction*="phone"] .Io6YTe'
            ]
            
            for selector in phone_selectors:
                try:
                    phone_element = await self.page.query_selector(selector)
                    if phone_element:
                        phone_text = await phone_element.inner_text()
                        if phone_text and phone_text.strip() and 'Send to phone' not in phone_text:
                            business_data['phone'] = phone_text.strip()
                            break
                except:
                    continue
            
            # Extract website with multiple selectors
            website_selectors = [
                'a[data-value="Website"]',
                'a[href^="http"][data-value="Website"]',
                'div[data-attrid="visit_website"] a',
                'a[jsaction*="website"]',
                'button[data-value="Website"] + div a',
                'div[jsaction*="pane.action"] a[href^="http"]'
            ]
            
            for selector in website_selectors:
                try:
                    website_element = await self.page.query_selector(selector)
                    if website_element:
                        website_href = await website_element.get_attribute('href')
                        if website_href and website_href.startswith('http'):
                            business_data['website'] = website_href
                            break
                except:
                    continue
            
            # Extract rating and reviews with better parsing
            rating_selectors = [
                'div.F7nice span[role="img"]',
                'span.ceNzKf[role="img"]',
                'span[role="img"][aria-label*="star"]',
                'div[jsaction*="rating"] span[role="img"]',
                'span[aria-label*="star"]'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = await self.page.query_selector(selector)
                    if rating_element:
                        aria_label = await rating_element.get_attribute('aria-label')
                        if aria_label:
                            import re
                            # Extract rating
                            rating_match = re.search(r'(\d+[.,]\d+)\s*(?:out of|stars?|★)', aria_label, re.IGNORECASE)
                            if rating_match:
                                business_data['rating'] = rating_match.group(1).replace(',', '.')
                            
                            # Extract review count from nearby elements
                            try:
                                # Look for review count near rating
                                review_elements = await self.page.query_selector_all('span.UY7F9, div.F7nice span, .ceNzKf ~ span')
                                for review_elem in review_elements:
                                    review_text = await review_elem.inner_text()
                                    review_match = re.search(r'([\d,]+)\s*(?:review|отзыв|reseña)', review_text, re.IGNORECASE)
                                    if review_match:
                                        business_data['reviews'] = review_match.group(1)
                                        break
                            except:
                                pass
                            break
                except:
                    continue
            
            # Extract category with better selectors
            category_selectors = [
                'button[jsaction="pane.rating.category"]',
                'div.DkEaL',
                'span.DkEaL',
                'div[data-attrid="category"]',
                'button[jsaction*="category"]',
                'div.mgr77e',
                'span.YhemCb'
            ]
            
            for selector in category_selectors:
                try:
                    category_element = await self.page.query_selector(selector)
                    if category_element:
                        category_text = await category_element.inner_text()
                        if category_text and category_text.strip():
                            business_data['category'] = category_text.strip()
                            break
                except:
                    continue
            
            if progress_callback:
                extracted_fields = [k for k, v in business_data.items() if v and k != 'keyword']
                progress_callback.emit(f"Extracted fields: {', '.join(extracted_fields)}")
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"Error extracting details: {str(e)}")
        
        return business_data
    
    async def close_browser(self):
        """Close the browser context"""
        if self.browser_context:
            await self.browser_context.close()


class ScrapingThread(QThread):
    """Thread for running the scraping process"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)  # number of results
    
    def __init__(self, keywords, chrome_path, profile_path, output_file):
        super().__init__()
        self.keywords = keywords
        self.chrome_path = chrome_path
        self.profile_path = profile_path
        self.output_file = output_file
        self.scraper = GoogleMapsScraper()
        self.is_running = True
        
    def stop(self):
        """Stop the scraping process"""
        self.is_running = False
        
    def run(self):
        """Run the scraping process"""
        try:
            asyncio.run(self._scrape_async())
        except Exception as e:
            self.progress_signal.emit(f"Error during scraping: {str(e)}")
        finally:
            self.finished_signal.emit(0)
    
    async def _scrape_async(self):
        """Async scraping function"""
        try:
            # Setup browser
            success = await self.scraper.setup_browser(
                self.chrome_path, self.profile_path, self.progress_signal
            )
            if not success:
                return
            
            all_results = []
            
            # Process each keyword
            for i, keyword in enumerate(self.keywords, 1):
                if not self.is_running:
                    break
                
                self.progress_signal.emit(f"Processing keyword {i}/{len(self.keywords)}: {keyword}")
                
                results = await self.scraper.search_keyword(keyword, self.progress_signal)
                all_results.extend(results)
                
                self.progress_signal.emit(f"Found {len(results)} businesses for '{keyword}'")
                
                # Random delay between keywords
                if i < len(self.keywords) and self.is_running:
                    delay = random.uniform(3, 6)
                    self.progress_signal.emit(f"Waiting {delay:.1f} seconds before next keyword...")
                    await asyncio.sleep(delay)
            
            # Save results
            if all_results:
                self._save_results(all_results, self.output_file)
                self.progress_signal.emit(f"✅ Scraping complete! Saved {len(all_results)} results to {self.output_file}")
                self.finished_signal.emit(len(all_results))
            else:
                self.progress_signal.emit("❌ No results found")
                self.finished_signal.emit(0)
                
        except Exception as e:
            self.progress_signal.emit(f"❌ Error: {str(e)}")
        finally:
            await self.scraper.close_browser()
    
    def _save_results(self, results: List[Dict[str, str]], output_file: str):
        """Save results to CSV file"""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['keyword', 'name', 'address', 'phone', 'website', 'rating', 'reviews', 'category']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
                    
            self.progress_signal.emit(f"Results saved to: {output_file}")
            
        except Exception as e:
            self.progress_signal.emit(f"Error saving results: {str(e)}")


class GoogleMapsScraperGUI(QMainWindow):
    """PyQt5 GUI interface for Google Maps scraper"""
    
    def __init__(self):
        super().__init__()
        self.scraping_thread = None
        self.init_ui()
        self.check_playwright_installation()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Google Maps Scraper v2.0 - PyQt5")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Google Maps Business Scraper")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # Create tabbed interface
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Configuration tab
        config_tab = self.create_config_tab()
        tabs.addTab(config_tab, "Configuration")
        
        # Progress tab
        progress_tab = self.create_progress_tab()
        tabs.addTab(progress_tab, "Progress & Results")
        
        # Control buttons
        self.create_control_buttons(layout)
        
        # Status bar
        self.statusBar().showMessage("Ready to scrape Google Maps")
        
        # Apply stylesheet
        self.apply_stylesheet()
        
    def create_config_tab(self):
        """Create the configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Keywords section
        keywords_group = QGroupBox("Keywords")
        keywords_layout = QVBoxLayout(keywords_group)
        
        QLabel("Enter keywords (one per line):").setParent(keywords_group)
        keywords_layout.addWidget(QLabel("Enter keywords (one per line):"))
        
        self.keywords_text = QTextEdit()
        self.keywords_text.setPlaceholderText("restaurants near me\ncoffee shops downtown\nauto repair shops")
        self.keywords_text.setMaximumHeight(150)
        keywords_layout.addWidget(self.keywords_text)
        
        # Load keywords button
        load_button = QPushButton("Load Keywords from File")
        load_button.clicked.connect(self.load_keywords_from_file)
        keywords_layout.addWidget(load_button)
        
        layout.addWidget(keywords_group)
        
        # Chrome settings section
        chrome_group = QGroupBox("Chrome Settings")
        chrome_layout = QGridLayout(chrome_group)
        
        # Chrome executable path
        chrome_layout.addWidget(QLabel("Chrome Executable Path:"), 0, 0)
        self.chrome_path_edit = QLineEdit("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        chrome_layout.addWidget(self.chrome_path_edit, 1, 0)
        chrome_browse_btn = QPushButton("Browse")
        chrome_browse_btn.clicked.connect(self.browse_chrome_path)
        chrome_layout.addWidget(chrome_browse_btn, 1, 1)
        
        # Chrome profile path
        chrome_layout.addWidget(QLabel("Chrome Profile Path:"), 2, 0)
        self.profile_path_edit = QLineEdit(str(Path.home() / "Library/Application Support/Google/Chrome"))
        chrome_layout.addWidget(self.profile_path_edit, 3, 0)
        profile_browse_btn = QPushButton("Browse")
        profile_browse_btn.clicked.connect(self.browse_profile_path)
        chrome_layout.addWidget(profile_browse_btn, 3, 1)
        
        layout.addWidget(chrome_group)
        
        # Output settings section
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout(output_group)
        
        output_layout.addWidget(QLabel("Output CSV File:"), 0, 0)
        self.output_file_edit = QLineEdit(str(Path.home() / "Desktop" / "google_maps_results.csv"))
        output_layout.addWidget(self.output_file_edit, 1, 0)
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(output_browse_btn, 1, 1)
        
        layout.addWidget(output_group)
        
        return tab
        
    def create_progress_tab(self):
        """Create the progress tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Progress text area
        progress_group = QGroupBox("Scraping Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: 'Courier New', monospace;")
        progress_layout.addWidget(self.progress_text)
        
        layout.addWidget(progress_group)
        
        return tab
        
    def create_control_buttons(self, layout):
        """Create control buttons"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_button = QPushButton("Start Scraping")
        self.start_button.setStyleSheet("QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 8px; }")
        self.start_button.clicked.connect(self.start_scraping)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; padding: 8px; }")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scraping)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def apply_stylesheet(self):
        """Apply custom stylesheet"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
        """)
        
    def check_playwright_installation(self):
        """Check if Playwright browsers are installed"""
        try:
            # Try to import and check basic functionality
            from playwright.async_api import async_playwright
            self.log_progress("Playwright is available")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Playwright Setup Required",
                "Playwright browsers may not be installed.\n\n"
                "Please run the following commands:\n"
                "1. pip install PyQt5 playwright\n"
                "2. python -m playwright install\n\n"
                "This will install the required Chrome browser."
            )
            
    def load_keywords_from_file(self):
        """Load keywords from a text file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Keywords File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    keywords = f.read()
                    self.keywords_text.setPlainText(keywords)
                    self.log_progress(f"Loaded keywords from: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
                
    def browse_chrome_path(self):
        """Browse for Chrome executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Chrome Executable",
            "/Applications",
            "All Files (*)"
        )
        
        if file_path:
            self.chrome_path_edit.setText(file_path)
            
    def browse_profile_path(self):
        """Browse for Chrome profile directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Chrome Profile Directory",
            str(Path.home())
        )
        
        if dir_path:
            self.profile_path_edit.setText(dir_path)
            
    def browse_output_file(self):
        """Browse for output CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results As",
            str(Path.home() / "Desktop" / "google_maps_results.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.output_file_edit.setText(file_path)
            
    def log_progress(self, message: str):
        """Log progress message to the GUI"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.progress_text.append(formatted_message)
        self.statusBar().showMessage(message)
        
    def start_scraping(self):
        """Start the scraping process"""
        # Validate inputs
        keywords = self.keywords_text.toPlainText().strip()
        if not keywords:
            QMessageBox.critical(self, "Error", "Please enter keywords or load them from a file")
            return
            
        chrome_path = self.chrome_path_edit.text().strip()
        profile_path = self.profile_path_edit.text().strip()
        output_file = self.output_file_edit.text().strip()
        
        if not chrome_path or not os.path.exists(chrome_path):
            QMessageBox.critical(self, "Error", "Please provide a valid Chrome executable path")
            return
            
        if not profile_path or not os.path.exists(profile_path):
            QMessageBox.critical(self, "Error", "Please provide a valid Chrome profile directory")
            return
            
        if not output_file:
            QMessageBox.critical(self, "Error", "Please provide an output file path")
            return
            
        # Parse keywords
        keyword_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        
        if not keyword_list:
            QMessageBox.critical(self, "Error", "No valid keywords found")
            return
            
        # Clear progress
        self.progress_text.clear()
        
        # Update UI state
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Start scraping thread
        self.scraping_thread = ScrapingThread(keyword_list, chrome_path, profile_path, output_file)
        self.scraping_thread.progress_signal.connect(self.log_progress)
        self.scraping_thread.finished_signal.connect(self.scraping_finished)
        self.scraping_thread.start()
        
        self.log_progress("🚀 Starting Google Maps scraping...")
        
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraping_thread:
            self.scraping_thread.stop()
            self.log_progress("🛑 Stopping scraping process...")
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def scraping_finished(self, result_count):
        """Handle scraping completion"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if result_count > 0:
            QMessageBox.information(
                self,
                "Scraping Complete",
                f"Successfully scraped {result_count} business listings!\n\n"
                f"Results saved to: {self.output_file_edit.text()}"
            )
        else:
            QMessageBox.warning(
                self,
                "No Results",
                "No business listings were found. Please try different keywords."
            )


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Google Maps Scraper")
    app.setOrganizationName("MapsScraper")
    
    # Create and show the main window
    window = GoogleMapsScraperGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
