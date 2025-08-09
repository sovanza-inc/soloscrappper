#!/usr/bin/env python3
"""
All In One Scraper Pro - Google Maps Scraper
Modern PyQt5 GUI Application with Professional Design
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
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QGridLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QFileDialog, 
        QMessageBox, QProgressBar, QGroupBox, QScrollArea, QFrame, QSplitter, 
        QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
        QSpinBox, QCheckBox, QSlider, QStatusBar, QMenuBar, QMenu, QAction,
        QSystemTrayIcon, QStyle, QDesktopWidget
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QLinearGradient
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
                progress_callback.emit("🚀 Setting up Chrome browser...")
                
            playwright = await async_playwright().start()
            
            # Create a unique profile directory to avoid conflicts
            import tempfile
            temp_profile = tempfile.mkdtemp(prefix="chrome_scraper_")
            
            if progress_callback:
                progress_callback.emit(f"📁 Using temporary profile: {temp_profile}")
            
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
                    "--no-default-browser-check"
                ]
            )
            
            # Create new page
            self.page = await self.browser_context.new_page()
            
            # Set realistic user agent
            await self.page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            if progress_callback:
                progress_callback.emit("✅ Chrome browser setup complete!")
                
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Error setting up browser: {str(e)}")
            return False
    
    async def search_keyword(self, keyword: str, progress_callback=None, business_callback=None) -> List[Dict[str, str]]:
        """ULTRA-FAST optimized search for a keyword on Google Maps"""
        if not self.page:
            return []
            
        try:
            if progress_callback:
                progress_callback.emit(f"🔍 Searching for: {keyword}")
                
            # Navigate to Google Maps with direct search URL
            search_url = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}"
            
            if progress_callback:
                progress_callback.emit(f"🌐 Navigating to: {search_url}")
            
            await self.page.goto(search_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            if progress_callback:
                progress_callback.emit("⏳ Waiting for results to load...")
            
            # Wait for results to load with multiple selectors
            selectors_to_try = [
                '[role="main"]',
                '.m6QErb',
                '[data-result-index]',
                'div[role="article"]'
            ]
            
            results_found = False
            for selector in selectors_to_try:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    results_found = True
                    if progress_callback:
                        progress_callback.emit(f"✅ Found results with selector: {selector}")
                    break
                except:
                    continue
            
            if not results_found:
                if progress_callback:
                    progress_callback.emit(f"❌ No results found for: {keyword}")
                return []
            
            # Scroll to load all results
            await self._scroll_results_panel(progress_callback)
            
            # Extract business listings with real-time callback
            businesses = await self._extract_business_listings_fast(keyword, progress_callback, business_callback)
            
            if progress_callback:
                progress_callback.emit(f"🎯 Extracted {len(businesses)} businesses for '{keyword}'")
            
            return businesses
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Error searching {keyword}: {str(e)}")
            return []
    
    async def _scroll_results_panel(self, progress_callback=None):
        """Scroll the results panel to load all businesses"""
        try:
            if progress_callback:
                progress_callback.emit("📜 Loading all results...")
                
            last_height = 0
            scroll_attempts = 0
            max_scrolls = 15
            
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
                
                await asyncio.sleep(random.uniform(1, 2))
                
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
                    progress_callback.emit(f"📜 Scrolling... ({scroll_attempts}/{max_scrolls})")
                    
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Error during scrolling: {str(e)}")
    
    async def _extract_business_listings_fast(self, keyword: str, progress_callback=None, business_callback=None) -> List[Dict[str, str]]:
        """Extract business information using improved method with better selectors"""
        businesses = []
        
        try:
            if progress_callback:
                progress_callback.emit("⚡ Extracting businesses with improved selectors...")
            
            # Wait for content to be fully loaded
            await asyncio.sleep(3)
            
            # Use improved extraction with multiple strategies
            businesses_data = await self.page.evaluate("""
                () => {
                    const businesses = [];
                    
                    // Try multiple selectors for business elements
                    const selectors = [
                        'div[role="article"]',
                        'div[jsaction*="pane.selectResult"]',
                        'a[data-cid]',
                        '.hfpxzc',
                        '[data-result-index]',
                        '.Nv2PK'
                    ];
                    
                    let businessElements = [];
                    for (const selector of selectors) {
                        businessElements = document.querySelectorAll(selector);
                        if (businessElements.length > 0) {
                            console.log(`Found ${businessElements.length} businesses with selector: ${selector}`);
                            break;
                        }
                    }
                    
                    businessElements.forEach((element, index) => {
                        if (index >= 100) return; // Limit to 100 results
                        
                        const business = {
                            name: '',
                            address: '',
                            phone: '',
                            website: '',
                            rating: '',
                            reviews: '',
                            category: ''
                        };
                        
                        try {
                            // Extract name with multiple selectors
                            const nameSelectors = [
                                '.DUwDvf.lfPIob',
                                'div[class*="fontHeadline"]',
                                'h3',
                                '.qBF1Pd',
                                '.dbg0pd div'
                            ];
                            
                            for (const sel of nameSelectors) {
                                const nameEl = element.querySelector(sel);
                                if (nameEl && nameEl.textContent.trim()) {
                                    business.name = nameEl.textContent.trim();
                                    break;
                                }
                            }
                            
                            // Extract address with multiple selectors
                            const addrSelectors = [
                                '.W4Efsd:last-child .W4Efsd',
                                '[data-value="Directions"]',
                                '.W4Efsd[data-value="Directions"]',
                                '.rogA2c .W4Efsd:last-child'
                            ];
                            
                            for (const sel of addrSelectors) {
                                const addrEl = element.querySelector(sel);
                                if (addrEl && addrEl.textContent.trim()) {
                                    business.address = addrEl.textContent.trim();
                                    break;
                                }
                            }
                            
                            // Extract rating
                            const ratingEl = element.querySelector('span.MW4etd, span[role="img"][aria-label*="star"]');
                            if (ratingEl) {
                                const ariaLabel = ratingEl.getAttribute('aria-label');
                                if (ariaLabel) {
                                    const match = ariaLabel.match(/([0-9.]+)/);
                                    if (match) business.rating = match[1];
                                } else {
                                    const ratingText = ratingEl.textContent.trim();
                                    const match = ratingText.match(/([0-9.]+)/);
                                    if (match) business.rating = match[1];
                                }
                            }
                            
                            // Extract reviews count
                            const reviewSelectors = [
                                '.UY7F9',
                                'span.RDApEe.YrbPuc',
                                'span[aria-label*="review"]'
                            ];
                            
                            for (const sel of reviewSelectors) {
                                const reviewEl = element.querySelector(sel);
                                if (reviewEl) {
                                    const reviewText = reviewEl.textContent || reviewEl.getAttribute('aria-label') || '';
                                    const match = reviewText.match(/([0-9,]+)/);
                                    if (match) {
                                        business.reviews = match[1];
                                        break;
                                    }
                                }
                            }
                            
                            // Extract category
                            const catSelectors = [
                                '.W4Efsd:first-child .W4Efsd',
                                '.DkEaL',
                                'span.DkEaL'
                            ];
                            
                            for (const sel of catSelectors) {
                                const catEl = element.querySelector(sel);
                                if (catEl && catEl.textContent.trim()) {
                                    business.category = catEl.textContent.trim();
                                    break;
                                }
                            }
                            
                        } catch (e) {
                            console.log('Error extracting business data:', e);
                        }
                        
                        // Only add if we have at least a name
                        if (business.name && business.name.length > 1) {
                            businesses.push(business);
                        }
                    });
                    
                    return businesses;
                }
            """);
            
            if progress_callback:
                progress_callback.emit(f"📊 Found {len(businesses_data)} businesses in total")
            
            # Process extracted data with real-time updates
            for i, business_data in enumerate(businesses_data):
                business_data['keyword'] = keyword
                businesses.append(business_data)
                
                if progress_callback:
                    progress_callback.emit(f"✅ Extracted: {business_data.get('name', 'Unknown')} ({i+1}/{len(businesses_data)})")
                
                if business_callback:
                    business_callback.emit(business_data)
                
                # Small delay to make updates visible
                await asyncio.sleep(0.1)
                    
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Error extracting listings: {str(e)}")
        
        return businesses
    
    async def close_browser(self):
        """Close the browser context"""
        if self.browser_context:
            await self.browser_context.close()


class ScrapingThread(QThread):
    """Thread for running the scraping process"""
    progress_signal = pyqtSignal(str)
    business_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(int)
    keyword_signal = pyqtSignal(str)  # New signal for current keyword updates
    
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
            self.progress_signal.emit(f"❌ Error during scraping: {str(e)}")
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
                
                # Emit current keyword signal
                self.keyword_signal.emit(keyword)
                self.progress_signal.emit(f"🔄 Processing keyword {i}/{len(self.keywords)}: {keyword}")
                
                results = await self.scraper.search_keyword(
                    keyword, self.progress_signal, self.business_signal
                )
                all_results.extend(results)
                
                self.progress_signal.emit(f"📊 Found {len(results)} businesses for '{keyword}'")
                
                # Random delay between keywords
                if i < len(self.keywords) and self.is_running:
                    delay = random.uniform(2, 4)
                    self.progress_signal.emit(f"⏱️ Waiting {delay:.1f} seconds before next keyword...")
                    await asyncio.sleep(delay)
            
            # Save results
            if all_results:
                self._save_results(all_results, self.output_file)
                self.progress_signal.emit(f"🎉 Scraping complete! Saved {len(all_results)} results to {self.output_file}")
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
                    
            self.progress_signal.emit(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            self.progress_signal.emit(f"❌ Error saving results: {str(e)}")


class ModernScraperGUI(QMainWindow):
    """Modern PyQt5 GUI interface for Google Maps scraper"""
    
    def __init__(self):
        super().__init__()
        self.scraping_thread = None
        self.scraped_businesses = []
        self.total_businesses = 0
        self.unique_businesses = 0
        
        self.init_ui()
        self.apply_modern_theme()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("All In One Scraper Pro - Making Your Life Easier")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Center window on screen
        self.center_window()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.create_header(main_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_google_maps_tab()
        self.create_scraped_data_tab()
        self.create_other_tabs()
        
        # Status bar
        self.create_status_bar()
        
    def center_window(self):
        """Center the window on the screen"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def create_header(self, main_layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(120)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Main title
        title_label = QLabel("All In One Scraper Pro")
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Subtitle
        subtitle_label = QLabel("Making Your Life Easier")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # License button
        license_btn = QPushButton("Add Licence Key")
        license_btn.setObjectName("licenseBtn")
        license_btn.clicked.connect(self.show_license_dialog)
        
        # Header layout
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(license_btn)
        
        header_layout.addLayout(title_layout)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
    def create_google_maps_tab(self):
        """Create the Google Maps scraper tab"""
        tab = QWidget()
        tab.setObjectName("googleMapsTab")
        layout = QHBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel - Input and controls
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # Keywords input
        keywords_label = QLabel("Enter Keywords (One per line):")
        keywords_label.setObjectName("sectionLabel")
        left_layout.addWidget(keywords_label)
        
        self.keywords_text = QTextEdit()
        self.keywords_text.setObjectName("keywordsInput")
        self.keywords_text.setPlaceholderText("restaurants near me\ncoffee shops downtown\nauto repair shops")
        self.keywords_text.setMaximumHeight(200)
        left_layout.addWidget(self.keywords_text)
        
        # Stats section
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QVBoxLayout(stats_frame)
        
        leads_label = QLabel("Leads Scraped:")
        leads_label.setObjectName("statsLabel")
        self.leads_count = QLabel("0")
        self.leads_count.setObjectName("statsNumber")
        
        keyword_label = QLabel("Current Keyword: None")
        keyword_label.setObjectName("currentKeyword")
        self.current_keyword_label = keyword_label
        
        stats_layout.addWidget(leads_label)
        stats_layout.addWidget(self.leads_count)
        stats_layout.addWidget(keyword_label)
        
        left_layout.addWidget(stats_frame)
        
        # Control buttons
        self.create_control_buttons(left_layout)
        
        # Business totals
        totals_frame = QFrame()
        totals_frame.setObjectName("totalsFrame")
        totals_layout = QVBoxLayout(totals_frame)
        
        self.total_label = QLabel("TOTAL Businesses: 0")
        self.total_label.setObjectName("totalLabel")
        self.unique_label = QLabel("UNIQUE Businesses: 0")
        self.unique_label.setObjectName("uniqueLabel")
        
        totals_layout.addWidget(self.total_label)
        totals_layout.addWidget(self.unique_label)
        
        left_layout.addWidget(totals_frame)
        left_layout.addStretch()
        
        # Right panel - Results table
        right_panel = self.create_results_table()
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, 1)
        
        self.tab_widget.addTab(tab, "Google Map Scraper")
        
    def create_control_buttons(self, layout):
        """Create control buttons"""
        # Scrape button
        scrape_btn = QPushButton("Scrape Websites")
        scrape_btn.setObjectName("scrapeBtn")
        scrape_btn.clicked.connect(self.start_scraping)
        layout.addWidget(scrape_btn)
        
        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.clicked.connect(self.pause_scraping)
        layout.addWidget(self.pause_btn)
        
        # Resume button
        self.resume_btn = QPushButton("Resume Scraping")
        self.resume_btn.setObjectName("resumeBtn")
        self.resume_btn.clicked.connect(self.resume_scraping)
        layout.addWidget(self.resume_btn)
        
        # Stop button
        self.stop_btn = QPushButton("Stop Scraping")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_scraping)
        layout.addWidget(self.stop_btn)
        
        # Save buttons
        save_all_btn = QPushButton("Save All to CSV")
        save_all_btn.setObjectName("saveAllBtn")
        save_all_btn.clicked.connect(self.save_all_csv)
        layout.addWidget(save_all_btn)
        
        save_unique_btn = QPushButton("Save Unique to CSV")
        save_unique_btn.setObjectName("saveUniqueBtn")
        save_unique_btn.clicked.connect(self.save_unique_csv)
        layout.addWidget(save_unique_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear Results")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self.clear_results)
        layout.addWidget(clear_btn)
        
    def create_results_table(self):
        """Create the results table"""
        frame = QFrame()
        frame.setObjectName("resultsFrame")
        layout = QVBoxLayout(frame)
        
        # Table
        self.results_table = QTableWidget()
        self.results_table.setObjectName("resultsTable")
        
        # Set columns
        columns = ["Keyword", "Business Name", "Website", "Phone Number", "Address", "Ratings", "Google Map Link", "Reviews", "Category"]
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(QLabel("Scraped Businesses Data:"))
        layout.addWidget(self.results_table)
        
        # Add progress log below the table
        log_label = QLabel("Scraping Progress & Logs:")
        log_label.setObjectName("sectionLabel")
        layout.addWidget(log_label)
        
        self.progress_log = QTextEdit()
        self.progress_log.setObjectName("progressLog")
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(200)
        layout.addWidget(self.progress_log)
        
        return frame
        
    def create_scraped_data_tab(self):
        """Create the scraped data tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel("Scraped Google Map Data")
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("tabTitle")
        layout.addWidget(label)
        
        # Placeholder for future data visualization
        data_label = QLabel("Data visualization and analytics coming soon...")
        data_label.setAlignment(Qt.AlignCenter)
        data_label.setObjectName("comingSoon")
        layout.addWidget(data_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Scraped Google Map Data")
        
    def create_other_tabs(self):
        """Create other placeholder tabs"""
        tab_names = [
            "Social Links Extractor",
            "Website Email Extractor", 
            "Combined Data",
            "Business Website Extractor",
            "Decision Makers Finder",
            "Captcha Free Scraping"
        ]
        
        for name in tab_names:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            label = QLabel(f"{name}\n\nComing Soon...")
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("comingSoon")
            layout.addWidget(label)
            
            self.tab_widget.addTab(tab, name)
            
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to scrape Google Maps")
        
    def apply_modern_theme(self):
        """Apply modern dark theme"""
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                color: white;
            }
            
            /* Header */
            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-bottom: 2px solid #3498db;
            }
            
            #mainTitle {
                font-size: 28px;
                font-weight: bold;
                color: white;
                margin: 10px;
            }
            
            #subtitle {
                font-size: 14px;
                color: #2ecc71;
                background: rgba(46, 204, 113, 0.2);
                padding: 5px 15px;
                border-radius: 15px;
                margin: 5px;
            }
            
            #licenseBtn {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                margin-right: 20px;
            }
            
            #licenseBtn:hover {
                background: #2980b9;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #34495e;
                background: #2c3e50;
            }
            
            QTabBar::tab {
                background: #5dade2;
                color: white;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background: #3498db;
            }
            
            QTabBar::tab:hover {
                background: #2980b9;
            }
            
            /* Left Panel */
            #leftPanel {
                background: rgba(52, 73, 94, 0.8);
                border-right: 2px solid #3498db;
                border-radius: 10px;
                margin: 5px;
            }
            
            /* Input Fields */
            #keywordsInput {
                background: #34495e;
                border: 2px solid #3498db;
                border-radius: 8px;
                color: white;
                font-size: 12px;
                padding: 10px;
            }
            
            /* Stats Frame */
            #statsFrame {
                background: rgba(46, 204, 113, 0.1);
                border: 2px solid #2ecc71;
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
            }
            
            #statsLabel {
                color: #2ecc71;
                font-weight: bold;
                font-size: 14px;
            }
            
            #statsNumber {
                color: white;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
            }
            
            #currentKeyword {
                color: #e74c3c;
                font-size: 12px;
                font-style: italic;
            }
            
            /* Control Buttons */
            #scrapeBtn {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
            }
            
            #scrapeBtn:hover {
                background: #27ae60;
            }
            
            #pauseBtn {
                background: #f39c12;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #pauseBtn:hover {
                background: #e67e22;
            }
            
            #resumeBtn {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #stopBtn {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #stopBtn:hover {
                background: #c0392b;
            }
            
            #saveAllBtn, #saveUniqueBtn {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #saveAllBtn:hover, #saveUniqueBtn:hover {
                background: #2980b9;
            }
            
            #clearBtn {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            /* Totals Frame */
            #totalsFrame {
                background: rgba(52, 152, 219, 0.1);
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
            }
            
            #totalLabel, #uniqueLabel {
                color: #3498db;
                font-weight: bold;
                font-size: 14px;
                margin: 5px 0;
            }
            
            /* Results Table */
            #resultsFrame {
                background: rgba(52, 73, 94, 0.8);
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            
            #resultsTable {
                background: #34495e;
                color: white;
                border: 1px solid #3498db;
                border-radius: 5px;
                gridline-color: #3498db;
            }
            
            #resultsTable::item {
                padding: 8px;
                border-bottom: 1px solid #3498db;
            }
            
            #resultsTable::item:selected {
                background: #3498db;
            }
            
            QHeaderView::section {
                background: #2980b9;
                color: white;
                padding: 10px;
                border: 1px solid #3498db;
                font-weight: bold;
            }
            
            /* Progress Log */
            #progressLog {
                background: #2c3e50;
                color: #2ecc71;
                border: 2px solid #3498db;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
            
            /* Coming Soon */
            #comingSoon {
                color: #bdc3c7;
                font-size: 18px;
                font-style: italic;
            }
            
            /* Section Labels */
            #sectionLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
                margin: 10px 0 5px 0;
            }
            
            /* Status Bar */
            QStatusBar {
                background: #34495e;
                color: white;
                border-top: 1px solid #3498db;
            }
        """)
        
    def show_license_dialog(self):
        """Show license key dialog"""
        QMessageBox.information(
            self, 
            "License Key", 
            "This is a free and open-source version.\n\nNo license key required!"
        )
        
    def start_scraping(self):
        """Start the scraping process"""
        keywords = self.keywords_text.toPlainText().strip()
        if not keywords:
            QMessageBox.warning(self, "Error", "Please enter keywords to scrape")
            return
            
        keyword_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
        
        if not keyword_list:
            QMessageBox.warning(self, "Error", "No valid keywords found")
            return
        
        # Chrome settings - using defaults for macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        profile_path = str(Path.home() / "Library/Application Support/Google/Chrome")
        output_file = str(Path.home() / "Desktop" / "google_maps_results.csv")
        
        # Clear previous results
        self.scraped_businesses = []
        self.results_table.setRowCount(0)
        self.progress_log.clear()
        
        # Start scraping thread
        self.scraping_thread = ScrapingThread(keyword_list, chrome_path, profile_path, output_file)
        self.scraping_thread.progress_signal.connect(self.log_progress)
        self.scraping_thread.business_signal.connect(self.add_business_to_table)
        self.scraping_thread.keyword_signal.connect(self.update_current_keyword)
        self.scraping_thread.finished_signal.connect(self.scraping_finished)
        self.scraping_thread.start()
        
        self.log_progress("🚀 Starting Google Maps scraping...")
        
    def pause_scraping(self):
        """Pause scraping process"""
        self.log_progress("⏸️ Scraping paused")
        
    def resume_scraping(self):
        """Resume scraping process"""
        self.log_progress("▶️ Scraping resumed")
        
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraping_thread:
            self.scraping_thread.stop()
            self.log_progress("🛑 Stopping scraping process...")
        
    def save_all_csv(self):
        """Save all results to CSV"""
        if not self.scraped_businesses:
            QMessageBox.warning(self, "No Data", "No businesses to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save All Results", 
            str(Path.home() / "Desktop" / "all_businesses.csv"),
            "CSV Files (*.csv)"
        )
        
        if file_path:
            self._save_to_csv(self.scraped_businesses, file_path)
            QMessageBox.information(self, "Success", f"Saved {len(self.scraped_businesses)} businesses to {file_path}")
            
    def save_unique_csv(self):
        """Save unique results to CSV"""
        if not self.scraped_businesses:
            QMessageBox.warning(self, "No Data", "No businesses to save")
            return
        
        # Remove duplicates based on business name and address
        unique_businesses = []
        seen = set()
        
        for business in self.scraped_businesses:
            key = (business.get('name', '').lower(), business.get('address', '').lower())
            if key not in seen and key != ('', ''):
                seen.add(key)
                unique_businesses.append(business)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Unique Results", 
            str(Path.home() / "Desktop" / "unique_businesses.csv"),
            "CSV Files (*.csv)"
        )
        
        if file_path:
            self._save_to_csv(unique_businesses, file_path)
            QMessageBox.information(self, "Success", f"Saved {len(unique_businesses)} unique businesses to {file_path}")
            
    def _save_to_csv(self, businesses, file_path):
        """Save businesses to CSV file"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['keyword', 'name', 'address', 'phone', 'website', 'rating', 'reviews', 'category']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for business in businesses:
                    writer.writerow(business)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")
            
    def clear_results(self):
        """Clear all results"""
        self.scraped_businesses = []
        self.results_table.setRowCount(0)
        self.progress_log.clear()
        self.total_businesses = 0
        self.unique_businesses = 0
        self.update_stats()
        self.log_progress("🗑️ Results cleared")
        
    def log_progress(self, message: str):
        """Log progress message"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.progress_log.append(formatted_message)
        self.status_bar.showMessage(message)
        
    def add_business_to_table(self, business_data: dict):
        """Add business to the results table"""
        self.scraped_businesses.append(business_data)
        
        # Add to table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        columns = ["keyword", "name", "website", "phone", "address", "rating", "", "reviews", "category"]
        
        for col, field in enumerate(columns):
            if field == "":
                item = QTableWidgetItem("N/A")  # Placeholder for Google Map Link
            else:
                item = QTableWidgetItem(str(business_data.get(field, '')))
            self.results_table.setItem(row, col, item)
        
        # Update stats
        self.total_businesses = len(self.scraped_businesses)
        self.leads_count.setText(str(self.total_businesses))
        
        # Calculate unique businesses
        seen = set()
        unique_count = 0
        for business in self.scraped_businesses:
            key = (business.get('name', '').lower(), business.get('address', '').lower())
            if key not in seen and key != ('', ''):
                seen.add(key)
                unique_count += 1
        
        self.unique_businesses = unique_count
        self.update_stats()
        
    def update_stats(self):
        """Update statistics display"""
        self.total_label.setText(f"TOTAL Businesses: {self.total_businesses}")
        self.unique_label.setText(f"UNIQUE Businesses: {self.unique_businesses}")
        
    def update_current_keyword(self, keyword: str):
        """Update the current keyword display"""
        self.current_keyword_label.setText(f"Current Keyword: {keyword}")
        
    def scraping_finished(self, result_count):
        """Handle scraping completion"""
        self.log_progress(f"🎉 Scraping completed! Total businesses found: {result_count}")
        self.current_keyword_label.setText("Current Keyword: Completed")
        
        if result_count > 0:
            QMessageBox.information(
                self, "Scraping Complete",
                f"Successfully scraped {result_count} business listings!\n\n"
                f"Total: {self.total_businesses}\n"
                f"Unique: {self.unique_businesses}"
            )


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("All In One Scraper Pro")
    app.setOrganizationName("ScraperPro")
    
    # Set application icon (if you have one)
    # app.setWindowIcon(QIcon('icon.png'))
    
    # Create and show the main window
    window = ModernScraperGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
