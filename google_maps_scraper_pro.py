#!/usr/bin/env python3
"""
Solo Scrapper Pro - Professional Web Scraping Tool
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
    """Professional web scraper using Playwright with real Chrome browser"""
    
    def __init__(self, scraping_thread=None):
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.results: List[Dict[str, str]] = []
        self.scraping_thread = scraping_thread
        
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
            
            # Use more lenient navigation settings for Google Maps
            if progress_callback:
                progress_callback.emit("🔄 Starting navigation to Google Maps...")
            
            # Try navigation with fallback strategies
            navigation_success = False
            for attempt in range(2):
                try:
                    if attempt == 0:
                        await self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                    else:
                        # Fallback: try with load event instead
                        if progress_callback:
                            progress_callback.emit("🔄 Retrying with different loading strategy...")
                        await self.page.goto(search_url, wait_until="load", timeout=45000)
                    
                    navigation_success = True
                    break
                except Exception as nav_error:
                    if attempt == 0:
                        if progress_callback:
                            progress_callback.emit(f"⚠ First navigation attempt failed: {str(nav_error)}")
                        continue
                    else:
                        raise nav_error
            
            if not navigation_success:
                raise Exception("Failed to navigate to Google Maps after multiple attempts")
            
            if progress_callback:
                progress_callback.emit("✅ Page loaded, waiting for content to stabilize...")
            
            await asyncio.sleep(1)  # Reduced wait time for dynamic content
            
            if progress_callback:
                progress_callback.emit("⏳ Waiting for results to load...")
            
            # Wait for results to load with multiple selectors
            selectors_to_try = [
                '[role="main"]',
                '.m6QErb',
                '[data-result-index]',
                'div[role="article"]',
                '.Nv2PK',  # Additional Google Maps selectors
                '.bJzME',
                '.lI9IFe'
            ]
            
            if progress_callback:
                progress_callback.emit(f"🔍 Trying {len(selectors_to_try)} different selectors to detect results...")
            
            results_found = False
            for i, selector in enumerate(selectors_to_try):
                try:
                    if progress_callback:
                        progress_callback.emit(f"🔍 Attempting selector {i+1}/{len(selectors_to_try)}: {selector}")
                    
                    await self.page.wait_for_selector(selector, timeout=8000)
                    results_found = True
                    if progress_callback:
                        progress_callback.emit(f"✅ Found results with selector: {selector}")
                    break
                except Exception as selector_error:
                    if progress_callback:
                        progress_callback.emit(f"❌ Selector {selector} failed: {str(selector_error)[:50]}...")
                    continue
            
            if not results_found:
                if progress_callback:
                    progress_callback.emit(f"❌ No results found for: {keyword} - All selectors failed")
                    progress_callback.emit(f"🔍 This might indicate: 1) No search results 2) Page didn't load properly 3) Google Maps changed their layout")
                return []
            
            # Check if paused before scrolling
            if self.scraping_thread:
                while self.scraping_thread.is_paused:
                    await asyncio.sleep(0.1)
                if not self.scraping_thread.is_running:
                    return []
            
            # Scroll to load all results
            await self._scroll_results_panel(progress_callback)
            
            # Extract business listings with real-time callback
            businesses = await self._extract_business_listings_fast(keyword, progress_callback, business_callback)
            
            if progress_callback:
                progress_callback.emit(f"🎯 Extracted {len(businesses)} businesses for '{keyword}'")
            
            return businesses
            
        except Exception as e:
            error_msg = str(e)
            if "Timeout" in error_msg:
                if progress_callback:
                    progress_callback.emit(f"⏰ Navigation timeout for {keyword}. This might be due to slow internet or Google Maps loading issues.")
                    progress_callback.emit(f"💡 Try: 1) Check internet connection 2) Wait a moment and retry 3) Use a different search term")
            else:
                if progress_callback:
                    progress_callback.emit(f"❌ Error searching {keyword}: {error_msg}")
            return []
    
    async def _scroll_results_panel(self, progress_callback=None):
        """Scroll the results panel to load all businesses"""
        try:
            if progress_callback:
                progress_callback.emit("📜 Loading all results...")
                
            last_business_count = 0
            scroll_attempts = 0
            max_scrolls = 25  # Increased from 15
            no_change_count = 0
            
            while scroll_attempts < max_scrolls:
                # Scroll down in the results panel more aggressively with multiple selectors
                await self.page.evaluate("""
                    () => {
                        // Try multiple selectors for the scrollable results panel
                        const selectors = [
                            '[role="main"]',
                            '.m6QErb',
                            '[data-value="Search results"]',
                            '.Nv2PK',
                            '.bJzME',
                            '.lI9IFe',
                            '[aria-label*="Results for"]',
                            '.section-scrollbox',
                            '.section-layout'
                        ];
                        
                        let scrolled = false;
                        for (const selector of selectors) {
                            const panel = document.querySelector(selector);
                            if (panel && panel.scrollHeight > panel.clientHeight) {
                                panel.scrollTop += 2000;  // Aggressive scroll
                                scrolled = true;
                                console.log(`Scrolled using selector: ${selector}`);
                                break;
                            }
                        }
                        
                        // Also try scrolling the entire page as fallback
                        window.scrollBy(0, 1000);
                        
                        // Try to click "Show more" or "Load more" buttons if they exist
                        const moreButtons = [
                            'button[aria-label*="more"]',
                            'button[aria-label*="More"]',
                            '.VfPpkd-LgbsSe[aria-label*="more"]',
                            '[data-value="Show more results"]'
                        ];
                        
                        for (const buttonSelector of moreButtons) {
                            const button = document.querySelector(buttonSelector);
                            if (button && button.offsetParent !== null) {
                                button.click();
                                console.log(`Clicked more button: ${buttonSelector}`);
                                break;
                            }
                        }
                        
                        return scrolled;
                    }
                """)
                
                await asyncio.sleep(random.uniform(0.3, 0.8))  # Optimized wait for content to load
                
                # Check if paused during scrolling
                if self.scraping_thread:
                    while self.scraping_thread.is_paused:
                        await asyncio.sleep(0.1)
                    if not self.scraping_thread.is_running:
                        return
                
                # Count current business listings with improved detection
                current_business_count = await self.page.evaluate("""
                    () => {
                        const selectors = [
                            'div[role="article"]',
                            '.m6QErb',
                            '[data-result-index]',
                            '.Nv2PK',
                            '.bJzME',
                            '.lI9IFe',
                            'a[data-cid]',
                            '[jsaction*="pane.resultCard"]',
                            '.section-result'
                        ];
                        
                        let maxCount = 0;
                        let bestSelector = '';
                        for (const selector of selectors) {
                            const elements = document.querySelectorAll(selector);
                            if (elements.length > maxCount) {
                                maxCount = elements.length;
                                bestSelector = selector;
                            }
                        }
                        
                        console.log(`Best selector: ${bestSelector} found ${maxCount} businesses`);
                        return maxCount;
                    }
                """)
                
                if progress_callback:
                    progress_callback.emit(f"📜 Scrolling... ({scroll_attempts+1}/{max_scrolls}) - Found {current_business_count} businesses")
                
                # Check if we found new businesses
                if current_business_count > last_business_count:
                    last_business_count = current_business_count
                    no_change_count = 0
                else:
                    no_change_count += 1
                    
                # Stop if no new businesses found for 3 consecutive attempts
                if no_change_count >= 3:
                    if progress_callback:
                        progress_callback.emit(f"📜 Scrolling complete - No new businesses found after {no_change_count} attempts")
                    break
                    
                scroll_attempts += 1
                
            if progress_callback:
                progress_callback.emit(f"📜 Scrolling finished - Total businesses detected: {current_business_count}")
                    
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Error during scrolling: {str(e)}")
    
    async def _extract_business_listings_fast(self, keyword: str, progress_callback=None, business_callback=None) -> List[Dict[str, str]]:
        """Extract business information using resilient multi-strategy approach"""
        businesses = []
        
        try:
            if progress_callback:
                progress_callback.emit("🔍 Using resilient extraction with click-through method...")
            
            # Wait for content to be fully loaded
            await asyncio.sleep(3)
            
            # Get all business listing elements using multiple strategies
            business_elements = await self._get_business_elements()
            
            if not business_elements:
                if progress_callback:
                    progress_callback.emit("❌ No business elements found")
                return []
            
            if progress_callback:
                progress_callback.emit(f"📊 Found {len(business_elements)} business listings to process")
            
            # Process each business by clicking and extracting detailed info
            for i, element_info in enumerate(business_elements):  # Process all businesses found
                # Check if paused before processing each business
                if self.scraping_thread:
                    while self.scraping_thread.is_paused:
                        await asyncio.sleep(0.1)
                    if not self.scraping_thread.is_running:
                        return businesses
                
                if progress_callback:
                    progress_callback.emit(f"🔄 Processing business {i+1}/{len(business_elements)}")
                
                try:
                    business_data = await self._extract_single_business(element_info, keyword, progress_callback)
                    
                    if business_data and business_data.get('name'):
                        businesses.append(business_data)
                        
                        if business_callback:
                            business_callback.emit(business_data)
                        
                        if progress_callback:
                            progress_callback.emit(f"✅ Extracted: {business_data.get('name', 'Unknown')}")
                    
                    # Minimal delay between extractions for speed
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    if progress_callback:
                        progress_callback.emit(f"⚠️ Error processing business {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Error in extraction process: {str(e)}")
        
        return businesses
    
    async def _get_business_elements(self):
        """Get business elements using Playwright's native element detection"""
        print("\n=== Starting business element detection ===")
        try:
            # Wait for results to load
            print("Waiting for main content to load...")
            await self.page.wait_for_selector('[role="main"]', timeout=10000)
            print("✓ Main content loaded successfully")
            
            # Multiple selectors for business listings - prioritized by reliability
            selectors = [
                'a[data-cid]',  # Most reliable - has business ID
                '.hfpxzc',  # Common business link class
                'a[href*="/maps/place/"]',  # Direct place links
                'div[role="article"] a',  # Article containers with links
                'div[jsaction*="selectResult"]',  # Elements with select action
                '[data-result-index] a',  # Indexed results
                'div[role="article"]'  # Fallback to article containers
            ]
            
            business_elements = []
            print(f"Trying {len(selectors)} different selectors...")
            
            for idx, selector in enumerate(selectors, 1):
                print(f"\n[{idx}/{len(selectors)}] Trying selector: '{selector}'")
                try:
                    # Use Playwright's native element detection
                    elements = await self.page.query_selector_all(selector)
                    
                    if elements:
                        print(f"  ✓ Found {len(elements)} elements")
                        visible_count = 0
                        processed_count = 0
                        
                        for i, element in enumerate(elements):  # Process all elements
                            try:
                                processed_count += 1
                                # Check if element is visible
                                is_visible = await element.is_visible()
                                
                                if is_visible:
                                    visible_count += 1
                                    # Get element text for identification
                                    text_content = await element.text_content()
                                    href = await element.get_attribute('href')
                                    data_cid = await element.get_attribute('data-cid')
                                    
                                    element_info = {
                                        'element': element,
                                        'selector': selector,
                                        'index': i,
                                        'text': (text_content or '').strip()[:100],
                                        'href': href or '',
                                        'has_data_cid': bool(data_cid)
                                    }
                                    
                                    business_elements.append(element_info)
                                    
                                    # Log first few elements for debugging
                                    if len(business_elements) <= 3:
                                        print(f"    [{len(business_elements)}] Text: '{element_info['text'][:50]}{'...' if len(element_info['text']) > 50 else ''}'")
                                        print(f"        Has data-cid: {element_info['has_data_cid']}, Has href: {bool(element_info['href'])}")
                                        
                            except Exception as e:
                                print(f"    ⚠ Error processing element {i}: {e}")
                                continue
                        
                        print(f"  → Processed {processed_count} elements, {visible_count} visible, {len(business_elements)} valid")
                        
                        if business_elements:
                            print(f"  ✓ Successfully found {len(business_elements)} business elements with selector '{selector}'")
                            break  # Use first successful strategy
                    else:
                        print(f"  ✗ No elements found")
                            
                except Exception as e:
                    print(f"  ✗ Error with selector '{selector}': {e}")
                    continue
            
            print(f"\n=== Element detection complete: {len(business_elements)} businesses found ===")
            return business_elements
            
        except Exception as e:
            print(f"✗ Critical error getting business elements: {e}")
            return []
    
    async def _extract_single_business(self, element_info, keyword, progress_callback=None):
        """Extract detailed information for a single business by clicking on it"""
        try:
            # Click on the business element
            click_success = await self._click_business_element(element_info)
            
            if not click_success:
                if progress_callback:
                    progress_callback.emit(f"⚠️ Failed to click on business: {element_info.get('text', 'Unknown')}")
                return None
            
            # Wait for details panel to load with better detection
            await self._wait_for_business_panel(progress_callback)
            
            # Extract detailed information from the side panel using Playwright methods
            if progress_callback:
                progress_callback.emit("🔍 Extracting business data...")
            
            business_data = await self._extract_business_data_native()
            
            if progress_callback:
                progress_callback.emit(f"📊 Raw extracted data: {business_data}")
            
            # Add keyword to the data
            if business_data:
                business_data['keyword'] = keyword
                
                if progress_callback:
                    progress_callback.emit(f"✅ Successfully extracted: {business_data.get('name', 'Unknown')}")
                    
                return business_data
            else:
                if progress_callback:
                    progress_callback.emit("⚠️ No business data extracted")
                return None
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"⚠️ Error extracting business details: {str(e)}")
            return None
    
    async def _click_business_element(self, element_info):
        """Click on a business element using Playwright's native click"""
        business_text = element_info.get('text', 'Unknown')[:50]
        print(f"\n🖱️  Attempting to click business: '{business_text}'")
        print(f"   Selector: {element_info.get('selector', 'N/A')}")
        print(f"   Index: {element_info.get('index', 'N/A')}")
        print(f"   Has data-cid: {element_info.get('has_data_cid', False)}")
        
        try:
            element = element_info['element']
            
            # Check if element is still attached to DOM
            try:
                is_attached = await element.evaluate('el => el.isConnected')
                if not is_attached:
                    print(f"   ✗ Element is no longer attached to DOM")
                    return False
            except Exception as attach_error:
                print(f"   ⚠ Could not check element attachment: {attach_error}")
            
            # Ensure element is still visible
            is_visible = await element.is_visible()
            print(f"   Visibility check: {'✓ Visible' if is_visible else '✗ Not visible'}")
            
            if is_visible:
                # Get element position for debugging
                try:
                    bbox = await element.bounding_box()
                    if bbox:
                        print(f"   Position: x={bbox['x']:.1f}, y={bbox['y']:.1f}, w={bbox['width']:.1f}, h={bbox['height']:.1f}")
                    else:
                        print(f"   ⚠ Could not get element bounding box")
                except Exception as bbox_error:
                    print(f"   ⚠ Error getting bounding box: {bbox_error}")
                
                # Scroll element into view if needed
                print(f"   📜 Scrolling element into view...")
                await element.scroll_into_view_if_needed()
                
                # Wait a moment for any animations
                await asyncio.sleep(0.5)
                
                # Use Playwright's native click with force option
                print(f"   🎯 Executing click...")
                await element.click(force=True)
                
                print(f"   ✅ Click successful!")
                return True
            else:
                print(f"   ✗ Element not visible, cannot click")
                return False
                
        except Exception as e:
            print(f"   ✗ Primary click failed: {e}")
            
            # Fallback: try clicking by selector
            print(f"   🔄 Attempting fallback click by selector...")
            try:
                selector = element_info['selector']
                index = element_info['index']
                
                print(f"   Fallback selector: '{selector}', index: {index}")
                
                # Try to find and click the element by selector
                elements = await self.page.query_selector_all(selector)
                print(f"   Found {len(elements)} elements with fallback selector")
                
                if index < len(elements):
                    fallback_element = elements[index]
                    is_fallback_visible = await fallback_element.is_visible()
                    print(f"   Fallback element visible: {is_fallback_visible}")
                    
                    if is_fallback_visible:
                        await fallback_element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await fallback_element.click(force=True)
                        print(f"   ✅ Fallback click successful!")
                        return True
                    else:
                        print(f"   ✗ Fallback element not visible")
                else:
                    print(f"   ✗ Index {index} out of range for fallback elements")
                    
            except Exception as fallback_error:
                print(f"   ✗ Fallback click also failed: {fallback_error}")
                
            print(f"   ❌ All click attempts failed")
            return False
    
    async def _extract_business_data_native(self):
        """Extract business data using Playwright's native methods"""
        print("\n📊 Starting business data extraction...")
        
        business_data = {
            'name': '',
            'address': '',
            'phone': '',
            'website': '',
            'rating': '',
            'reviews': '',
            'category': ''
        }
        
        try:
            # Extract name - multiple strategies
            print("\n🏢 Extracting business name...")
            name_selectors = [
                'h1[data-attrid="title"]',
                'h1.DUwDvf',
                '.x3AX1-LfntMc-header-title h1',
                '[data-attrid="title"]',
                'h1',
                '.qBF1Pd.fontHeadlineSmall'
            ]
            
            for i, selector in enumerate(name_selectors, 1):
                print(f"   [{i}/{len(name_selectors)}] Trying name selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text and text.strip():
                            business_data['name'] = text.strip()
                            print(f"   ✅ Found name: '{business_data['name']}'")
                            break
                        else:
                            print(f"   ⚠ Element found but no text content")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            if not business_data['name']:
                print("   ❌ No business name found with any selector")
            
            # Extract address
            print("\n📍 Extracting business address...")
            address_selectors = [
                '[data-item-id="address"] .Io6YTe',
                '[data-attrid="kc:/location/location:address"]',
                '.LrzXr',
                '[data-value="Directions"]',
                'button[data-value="Directions"] .Io6YTe',
                '.rogA2c .Io6YTe'
            ]
            
            for i, selector in enumerate(address_selectors, 1):
                print(f"   [{i}/{len(address_selectors)}] Trying address selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text and text.strip():
                            business_data['address'] = text.strip()
                            print(f"   ✅ Found address: '{business_data['address']}'")
                            break
                        else:
                            print(f"   ⚠ Element found but no text content")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            if not business_data['address']:
                print("   ❌ No business address found with any selector")
            
            # Extract phone number
            print("\n📞 Extracting business phone...")
            phone_selectors = [
                # Primary phone selectors
                '[data-item-id="phone"] .Io6YTe',
                'button[data-value*="tel:"] .Io6YTe',
                'a[href^="tel:"]',
                '[data-attrid*="phone"]',
                # Additional comprehensive selectors
                'button[jsaction*="phone"] .Io6YTe',
                '.rogA2c button[data-value*="tel:"]',
                '.CsEnBe[aria-label*="phone"]',
                '.CsEnBe[aria-label*="Phone"]',
                'button[aria-label*="phone"] .Io6YTe',
                'button[aria-label*="Phone"] .Io6YTe',
                '.Io6YTe[aria-label*="phone"]',
                '.Io6YTe[aria-label*="Phone"]',
                # Fallback selectors
                'a[href*="tel:"]',
                'span[aria-label*="phone"]',
                'span[aria-label*="Phone"]',
                # Generic phone pattern selectors
                'button:has-text("+")',
                'span:has-text("+")',
                '.Io6YTe:has-text("+")',
                # Contact section selectors
                '[data-value="Call"] .Io6YTe',
                'button[data-value="Call"] .Io6YTe'
            ]
            
            for i, selector in enumerate(phone_selectors, 1):
                print(f"   [{i}/{len(phone_selectors)}] Trying phone selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        href = await element.get_attribute('href')
                        aria_label = await element.get_attribute('aria-label')
                        
                        # Try multiple sources for phone text
                        phone_sources = [
                            text,
                            href.replace('tel:', '') if href and href.startswith('tel:') else '',
                            aria_label
                        ]
                        
                        phone_text = ''
                        for source in phone_sources:
                            if source and source.strip():
                                phone_text = source.strip()
                                break
                        
                        print(f"   Raw phone text: '{phone_text}', href: '{href}', aria-label: '{aria_label}'")
                        
                        if phone_text:
                            import re
                            # More comprehensive phone pattern matching
                            phone_patterns = [
                                r'\+?[0-9\s\-\(\)]{7,}',  # General phone pattern
                                r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}',  # International
                                r'\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',  # US format
                                r'\d{2,4}[\s\-]\d{3,4}[\s\-]\d{3,4}',  # General format
                                r'[0-9\+\-\(\)\s]{7,}'  # Fallback pattern
                            ]
                            
                            for pattern in phone_patterns:
                                match = re.search(pattern, phone_text)
                                if match:
                                    found_phone = match.group(0).strip()
                                    # Validate it has enough digits
                                    digit_count = len(re.findall(r'\d', found_phone))
                                    if digit_count >= 7:  # Minimum 7 digits for a valid phone
                                        business_data['phone'] = found_phone
                                        print(f"   ✅ Found phone: '{business_data['phone']}' (pattern: {pattern})")
                                        break
                            
                            if business_data['phone']:
                                break
                            else:
                                digit_count = len(re.findall(r'\d', phone_text))
                                print(f"   ⚠ Text found but no valid phone pattern match (digits: {digit_count})")
                        else:
                            print(f"   ⚠ Element found but no phone text")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            # Additional fallback: search for phone patterns in all visible text
            if not business_data['phone']:
                print("   🔍 Fallback: Searching for phone patterns in all visible text...")
                try:
                    # Get all text content from the business details panel
                    panel_text = await self.page.evaluate('''
                        () => {
                            const panel = document.querySelector('[role="main"]') || document.body;
                            return panel.innerText || panel.textContent || '';
                        }
                    ''')
                    
                    if panel_text:
                        import re
                        # Look for phone patterns in the full text
                        phone_patterns = [
                            r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}',
                            r'\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',
                            r'\d{2,4}[\s\-]\d{3,4}[\s\-]\d{3,4}'
                        ]
                        
                        for pattern in phone_patterns:
                            matches = re.findall(pattern, panel_text)
                            for match in matches:
                                digit_count = len(re.findall(r'\d', match))
                                if digit_count >= 7:
                                    business_data['phone'] = match.strip()
                                    print(f"   ✅ Found phone in text: '{business_data['phone']}'")
                                    break
                            if business_data['phone']:
                                break
                except Exception as e:
                    print(f"   ⚠ Error in fallback phone search: {e}")
            
            if not business_data['phone']:
                print("   ❌ No business phone found with any method")
            
            # Extract website
            print("\n🌐 Extracting business website...")
            website_selectors = [
                '[data-item-id="authority"] a',
                'a[data-value="Website"]',
                'a[href^="http"]:not([href*="google.com"]):not([href*="maps"])',
                '[data-attrid*="website"] a'
            ]
            
            for i, selector in enumerate(website_selectors, 1):
                print(f"   [{i}/{len(website_selectors)}] Trying website selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        href = await element.get_attribute('href')
                        print(f"   Found href: '{href}'")
                        if href and 'google.com' not in href and 'maps' not in href:
                            business_data['website'] = href
                            print(f"   ✅ Found website: '{business_data['website']}'")
                            break
                        else:
                            print(f"   ⚠ Href found but contains google.com or maps")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            if not business_data['website']:
                print("   ❌ No business website found with any selector")
            
            # Extract rating
            print("\n⭐ Extracting business rating...")
            rating_selectors = [
                '.F7nice span[aria-hidden="true"]',
                'span.ceNzKf[aria-label*="star"]',
                '.MW4etd',
                '[role="img"][aria-label*="star"]'
            ]
            
            for i, selector in enumerate(rating_selectors, 1):
                print(f"   [{i}/{len(rating_selectors)}] Trying rating selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        aria_label = await element.get_attribute('aria-label')
                        
                        rating_text = text or aria_label or ''
                        print(f"   Raw rating text: '{rating_text}', aria-label: '{aria_label}'")
                        
                        import re
                        match = re.search(r'([0-9]\.[0-9])', rating_text)
                        if match:
                            business_data['rating'] = match.group(1)
                            print(f"   ✅ Found rating: '{business_data['rating']}'")
                            break
                        else:
                            print(f"   ⚠ Text found but no rating pattern match")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            if not business_data['rating']:
                print("   ❌ No business rating found with any selector")
            
            # Extract reviews count
            print("\n📝 Extracting business reviews count...")
            review_selectors = [
                '.F7nice .RDApEe',
                '.UY7F9',
                'button[jsaction*="reviews"] .RDApEe',
                '[aria-label*="review"]'
            ]
            
            for i, selector in enumerate(review_selectors, 1):
                print(f"   [{i}/{len(review_selectors)}] Trying reviews selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        aria_label = await element.get_attribute('aria-label')
                        
                        review_text = text or aria_label or ''
                        print(f"   Raw reviews text: '{review_text}', aria-label: '{aria_label}'")
                        
                        import re
                        match = re.search(r'([0-9,]+)', review_text)
                        if match:
                            business_data['reviews'] = match.group(1).replace(',', '')
                            print(f"   ✅ Found reviews count: '{business_data['reviews']}'")
                            break
                        else:
                            print(f"   ⚠ Text found but no number pattern match")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            if not business_data['reviews']:
                print("   ❌ No business reviews count found with any selector")
            
            # Extract category
            print("\n🏷️ Extracting business category...")
            category_selectors = [
                'button[jsaction*="category"] .DkEaL',
                '.DkEaL',
                '[data-attrid*="category"]',
                '.YhemCb .DkEaL'
            ]
            
            for i, selector in enumerate(category_selectors, 1):
                print(f"   [{i}/{len(category_selectors)}] Trying category selector: '{selector}'")
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        print(f"   Found category text: '{text}'")
                        if text and text.strip():
                            business_data['category'] = text.strip()
                            print(f"   ✅ Found category: '{business_data['category']}'")
                            break
                        else:
                            print(f"   ⚠ Element found but no text content")
                    else:
                        print(f"   ✗ No element found")
                except Exception as e:
                    print(f"   ⚠ Error with selector: {e}")
                    continue
            
            if not business_data['category']:
                print("   ❌ No business category found with any selector")
            
            print(f"\n🎯 Final extracted data summary:")
            print(f"   Name: '{business_data['name']}'")
            print(f"   Address: '{business_data['address']}'")
            print(f"   Phone: '{business_data['phone']}'")
            print(f"   Website: '{business_data['website']}'")
            print(f"   Rating: '{business_data['rating']}'")
            print(f"   Reviews: '{business_data['reviews']}'")
            print(f"   Category: '{business_data['category']}'")
            
        except Exception as e:
            print(f"❌ Error extracting business data: {e}")
        
        return business_data
    
    async def _wait_for_business_panel(self, progress_callback=None):
        """Wait for business details panel to load properly"""
        try:
            if progress_callback:
                progress_callback.emit("⏳ Waiting for business details to load...")
            
            # Wait for any of these elements that indicate the panel has loaded
            panel_indicators = [
                'h1[data-attrid="title"]',  # Business name
                'h1.DUwDvf',  # Alternative business name
                '[data-item-id="address"]',  # Address section
                '.F7nice',  # Rating section
                'h1'  # Fallback to any h1
            ]
            
            # Try to wait for panel indicators with timeout
            for selector in panel_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    if progress_callback:
                        progress_callback.emit("✅ Business details panel loaded")
                    
                    # Reduced wait for content to stabilize
                    await asyncio.sleep(0.3)
                    return True
                except:
                    continue
            
            # If no specific indicators found, wait a bit more
            if progress_callback:
                progress_callback.emit("⚠️ Panel indicators not found, using fallback wait")
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"⚠️ Error waiting for panel: {str(e)}")
            await asyncio.sleep(1)  # Reduced fallback wait
            return False
    
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
        self.scraper = GoogleMapsScraper(self)
        self.is_running = True
        self.is_paused = False
        
    def stop(self):
        """Stop the scraping process"""
        self.is_running = False
        self.is_paused = False
        
    def pause(self):
        """Pause the scraping process"""
        self.is_paused = True
        
    def resume(self):
        """Resume the scraping process"""
        self.is_paused = False
        
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
                
                # Check for pause state
                while self.is_paused and self.is_running:
                    await asyncio.sleep(0.5)  # Wait while paused
                
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
                
                # Reduced delay between keywords for speed
                if i < len(self.keywords) and self.is_running:
                    delay = random.uniform(0.5, 1.5)
                    self.progress_signal.emit(f"⏱️ Waiting {delay:.1f} seconds before next keyword...")
                    
                    # Respect pause during delay
                    delay_start = time.time()
                    while time.time() - delay_start < delay and self.is_running:
                        if self.is_paused:
                            while self.is_paused and self.is_running:
                                await asyncio.sleep(0.5)
                            if not self.is_running:
                                break
                        await asyncio.sleep(0.1)
            
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
                fieldnames = ['keyword', 'name', 'address', 'phone', 'website', 'rating', 'category']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
                    
            self.progress_signal.emit(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            self.progress_signal.emit(f"❌ Error saving results: {str(e)}")


class ModernScraperGUI(QMainWindow):
    """Modern PyQt5 GUI interface for Solo Scrapper"""
    
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
        self.setWindowTitle("Solo Scrapper - Making Your Life Easier")
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
        self.create_dashboard_tab()
        self.create_google_maps_tab()
        
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
        
        # Top row with logo, title and license button
        top_row_layout = QHBoxLayout()
        
        # Logo image
        logo_label = QLabel()
        logo_pixmap = QPixmap("launchericonplain.png")
        if not logo_pixmap.isNull():
            # Scale the logo to fit nicely in header
            scaled_pixmap = logo_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setObjectName("logoLabel")
        
        # Main title (left-aligned)
        title_label = QLabel("Solo Scrapper")
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # License button
        license_btn = QPushButton("Add Licence Key")
        license_btn.setObjectName("licenseBtn")
        license_btn.clicked.connect(self.show_license_dialog)
        
        # Add widgets to top row
        top_row_layout.addWidget(logo_label)
        top_row_layout.addSpacing(15)  # Space between logo and title
        top_row_layout.addWidget(title_label)
        top_row_layout.addStretch()  # Push license button to the right
        top_row_layout.addWidget(license_btn)
        
        # Subtitle (centered)
        subtitle_label = QLabel("Professional Web Scraping Tool")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addLayout(top_row_layout)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)

    def create_dashboard_tab(self):
        """Create the dashboard tab with real-time statistics"""
        tab = QWidget()
        tab.setObjectName("dashboardTab")
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Dashboard title
        title_label = QLabel("📊 Scraping Dashboard")
        title_label.setObjectName("dashboardTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Statistics grid
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(8)
        
        # Total businesses card
        self.total_businesses_card = self.create_stat_card("Total Businesses", "0", "📈")
        stats_layout.addWidget(self.total_businesses_card, 0, 0)
        
        # Unique businesses card
        self.unique_businesses_card = self.create_stat_card("Unique Businesses", "0", "🎯")
        stats_layout.addWidget(self.unique_businesses_card, 0, 1)
        
        # Success rate card
        self.success_rate_card = self.create_stat_card("Success Rate", "0%", "✅")
        stats_layout.addWidget(self.success_rate_card, 0, 2)
        
        # Current keyword card
        self.current_keyword_card = self.create_stat_card("Current Keyword", "Ready", "🔍")
        stats_layout.addWidget(self.current_keyword_card, 1, 0)
        
        # Keywords processed card
        self.keywords_processed_card = self.create_stat_card("Keywords Processed", "0", "📝")
        stats_layout.addWidget(self.keywords_processed_card, 1, 1)
        
        # Scraping status card
        self.scraping_status_card = self.create_stat_card("Status", "Idle", "⏸️")
        stats_layout.addWidget(self.scraping_status_card, 1, 2)
        
        layout.addWidget(stats_frame)
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        
        progress_title = QLabel("📊 Real-time Progress")
        progress_title.setObjectName("sectionLabel")
        progress_layout.addWidget(progress_title)
        
        # Progress bar
        self.dashboard_progress_bar = QProgressBar()
        self.dashboard_progress_bar.setObjectName("dashboardProgressBar")
        self.dashboard_progress_bar.setTextVisible(True)
        self.dashboard_progress_bar.setFormat("Ready to start scraping...")
        progress_layout.addWidget(self.dashboard_progress_bar)
        
        # Recent activity log
        activity_title = QLabel("📋 Recent Activity")
        activity_title.setObjectName("sectionLabel")
        progress_layout.addWidget(activity_title)
        
        self.dashboard_activity_log = QTextEdit()
        self.dashboard_activity_log.setObjectName("dashboardActivityLog")
        self.dashboard_activity_log.setReadOnly(True)
        self.dashboard_activity_log.setMaximumHeight(120)
        self.dashboard_activity_log.append("[Dashboard] Ready to start scraping...")
        progress_layout.addWidget(self.dashboard_activity_log)
        
        layout.addWidget(progress_frame)
        
        # Initialize dashboard tracking variables
        self.keywords_processed_count = 0
        self.current_scraping_status = "Idle"
        
        self.tab_widget.addTab(tab, "📊 Dashboard")
        
    def create_stat_card(self, title, value, icon):
        """Create a statistics card widget"""
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("statIcon")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        header_layout.addWidget(title_label)
        
        card_layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        
        return card

    def create_google_maps_tab(self):
        """Create the main scraper tab"""
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
        
        # Removed stats section for cleaner interface
        
        # Control buttons
        self.create_control_buttons(left_layout)
        
        # Removed business totals section for cleaner interface
        
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
        columns = ["Keyword", "Business Name", "Website", "Phone Number", "Address", "Ratings", "Category"]
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
        

        

            
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to scrape Google Maps")
        
    def apply_modern_theme(self):
        """Apply modern ultra-dark theme"""
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0d1117, stop:1 #161b22);
                color: #f0f6fc;
            }
            
            /* Header */
            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #161b22, stop:1 #0d1117);
                border-bottom: 2px solid #7c3aed;
            }
            
            #mainTitle {
                font-size: 28px;
                font-weight: bold;
                color: #f0f6fc;
                margin: 10px;
            }
            
            #logoLabel {
                margin: 10px;
                padding: 5px;
            }
            
            #subtitle {
                font-size: 14px;
                color: #7c3aed;
                background: rgba(124, 58, 237, 0.15);
                padding: 5px 15px;
                border-radius: 15px;
                margin: 5px;
            }
            
            #licenseBtn {
                background: #7c3aed;
                color: #f0f6fc;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                margin-right: 20px;
            }
            
            #licenseBtn:hover {
                background: #6d28d9;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #21262d;
                background: #0d1117;
            }
            
            QTabBar::tab {
                background: #21262d;
                color: #f0f6fc;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background: #7c3aed;
            }
            
            QTabBar::tab:hover {
                background: #30363d;
            }
            
            /* Left Panel */
            #leftPanel {
                background: rgba(13, 17, 23, 0.9);
                border-right: 2px solid #7c3aed;
                border-radius: 10px;
                margin: 5px;
            }
            
            /* Input Fields */
            #keywordsInput {
                background: #21262d;
                border: 2px solid #7c3aed;
                border-radius: 8px;
                color: #f0f6fc;
                font-size: 12px;
                padding: 10px;
            }
            
            /* Removed stats frame styling for cleaner interface */
            
            /* Control Buttons */
            #scrapeBtn {
                background: #238636;
                color: #f0f6fc;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 0;
            }
            
            #scrapeBtn:hover {
                background: #2ea043;
            }
            
            #pauseBtn {
                background: #fb8500;
                color: #f0f6fc;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #pauseBtn:hover {
                background: #ffb700;
            }
            
            #resumeBtn {
                background: #238636;
                color: #f0f6fc;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #stopBtn {
                background: #da3633;
                color: #f0f6fc;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #stopBtn:hover {
                background: #f85149;
            }
            
            #saveAllBtn, #saveUniqueBtn {
                background: #7c3aed;
                color: #f0f6fc;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            #saveAllBtn:hover, #saveUniqueBtn:hover {
                background: #6d28d9;
            }
            
            #clearBtn {
                background: #da3633;
                color: #f0f6fc;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin: 2px 0;
            }
            
            /* Removed totals frame styling for cleaner interface */
            
            /* Results Table */
            #resultsFrame {
                background: rgba(13, 17, 23, 0.9);
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            
            #resultsTable {
                background: #21262d;
                color: #f0f6fc;
                border: 1px solid #7c3aed;
                border-radius: 5px;
                gridline-color: #7c3aed;
            }
            
            #resultsTable::item {
                padding: 8px;
                border-bottom: 1px solid #30363d;
            }
            
            #resultsTable::item:selected {
                background: #7c3aed;
            }
            
            QHeaderView::section {
                background: #6d28d9;
                color: #f0f6fc;
                padding: 10px;
                border: 1px solid #7c3aed;
                font-weight: bold;
            }
            
            /* Progress Log */
            #progressLog {
                background: #0d1117;
                color: #7c3aed;
                border: 2px solid #7c3aed;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
            
            /* Coming Soon */
            #comingSoon {
                color: #8b949e;
                font-size: 18px;
                font-style: italic;
            }
            
            /* Section Labels */
            #sectionLabel {
                color: #f0f6fc;
                font-weight: bold;
                font-size: 14px;
                margin: 10px 0 5px 0;
            }
            
            /* Status Bar */
            QStatusBar {
                background: #21262d;
                color: #f0f6fc;
                border-top: 1px solid #7c3aed;
            }
            
            /* Dashboard Styles */
            #dashboardTitle {
                font-size: 18px;
                font-weight: bold;
                color: #f0f6fc;
                margin: 10px 0;
                padding: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #6d28d9);
                border-radius: 6px;
            }
            
            #statsFrame {
                background: rgba(13, 17, 23, 0.9);
                border: 1px solid #7c3aed;
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
            }
            
            #statCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21262d, stop:1 #161b22);
                border: 1px solid #7c3aed;
                border-radius: 6px;
                padding: 8px;
                min-height: 60px;
                max-height: 70px;
                min-width: 140px;
            }
            
            #statCard:hover {
                border-color: #6d28d9;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #30363d, stop:1 #21262d);
            }
            
            #statIcon {
                font-size: 14px;
                margin-right: 5px;
            }
            
            #statTitle {
                color: #8b949e;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
            }
            
            #statValue {
                color: #f0f6fc;
                font-size: 16px;
                font-weight: bold;
                margin-top: 5px;
            }
            
            #progressFrame {
                background: rgba(13, 17, 23, 0.9);
                border: 1px solid #7c3aed;
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
            }
            
            #dashboardProgressBar {
                background: #21262d;
                border: 1px solid #7c3aed;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                color: #f0f6fc;
                height: 20px;
            }
            
            #dashboardProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #6d28d9);
                border-radius: 3px;
            }
            
            #dashboardActivityLog {
                background: #0d1117;
                color: #7c3aed;
                border: 1px solid #7c3aed;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 9px;
                padding: 5px;
                max-height: 120px;
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
        
        # Connect dashboard signals
        self.scraping_thread.progress_signal.connect(self.update_dashboard_activity)
        self.scraping_thread.business_signal.connect(self.update_dashboard_stats)
        self.scraping_thread.keyword_signal.connect(self.update_dashboard_keyword)
        self.scraping_thread.start()
        
        self.log_progress("🚀 Starting Google Maps scraping...")
        
    def pause_scraping(self):
        """Pause scraping process"""
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.pause()
            self.log_progress("⏸️ Scraping paused")
        else:
            self.log_progress("⚠️ No active scraping process to pause")
        
    def resume_scraping(self):
        """Resume scraping process"""
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.resume()
            self.log_progress("▶️ Scraping resumed")
        else:
            self.log_progress("⚠️ No paused scraping process to resume")
        
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.stop()
            self.log_progress("🛑 Stopping scraping process...")
        else:
            self.log_progress("⚠️ No active scraping process to stop")
        
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
        
        # Reset dashboard
        if hasattr(self, 'total_businesses_card'):
            total_value = self.total_businesses_card.findChild(QLabel, "statValue")
            unique_value = self.unique_businesses_card.findChild(QLabel, "statValue")
            success_value = self.success_rate_card.findChild(QLabel, "statValue")
            keyword_value = self.current_keyword_card.findChild(QLabel, "statValue")
            processed_value = self.keywords_processed_card.findChild(QLabel, "statValue")
            status_value = self.scraping_status_card.findChild(QLabel, "statValue")
            
            if total_value: total_value.setText("0")
            if unique_value: unique_value.setText("0")
            if success_value: success_value.setText("0%")
            if keyword_value: keyword_value.setText("Ready")
            if processed_value: processed_value.setText("0")
            if status_value: status_value.setText("⏸️ Idle")
        
        # Reset dashboard progress and activity
        if hasattr(self, 'dashboard_progress_bar'):
            self.dashboard_progress_bar.setValue(0)
            self.dashboard_progress_bar.setFormat("Ready to start scraping...")
        
        if hasattr(self, 'dashboard_activity_log'):
            self.dashboard_activity_log.clear()
            self.dashboard_activity_log.append("[Dashboard] Ready to start scraping...")
        
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
        
        columns = ["keyword", "name", "website", "phone", "address", "rating", "category"]
        
        for col, field in enumerate(columns):
            item = QTableWidgetItem(str(business_data.get(field, '')))
            self.results_table.setItem(row, col, item)
        
        # Update stats
        self.total_businesses = len(self.scraped_businesses)
        # Removed leads count display for cleaner interface
        
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
        # Removed business totals display for cleaner interface
        pass
    
    def update_dashboard_activity(self, message: str):
        """Update dashboard activity log"""
        if hasattr(self, 'dashboard_activity_log'):
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.dashboard_activity_log.append(formatted_message)
            # Keep only last 50 messages for performance
            if self.dashboard_activity_log.document().blockCount() > 50:
                cursor = self.dashboard_activity_log.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.select(cursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deletePreviousChar()  # Remove the newline
    
    def update_dashboard_stats(self, business_data: dict):
        """Update dashboard statistics when a new business is found"""
        if hasattr(self, 'total_businesses_card'):
            # Find the value labels in the stat cards
            total_value = self.total_businesses_card.findChild(QLabel, "statValue")
            unique_value = self.unique_businesses_card.findChild(QLabel, "statValue")
            success_value = self.success_rate_card.findChild(QLabel, "statValue")
            
            if total_value:
                total_value.setText(str(self.total_businesses))
            if unique_value:
                unique_value.setText(str(self.unique_businesses))
            if success_value and self.total_businesses > 0:
                success_rate = (self.unique_businesses / self.total_businesses) * 100
                success_value.setText(f"{success_rate:.1f}%")
            
            # Update progress bar
            if hasattr(self, 'scraping_thread') and self.scraping_thread:
                total_keywords = len(self.scraping_thread.keywords)
                # Estimate progress based on current activity
                current_progress = min(95, (self.total_businesses / max(1, total_keywords * 10)) * 100)
                self.dashboard_progress_bar.setValue(int(current_progress))
                self.dashboard_progress_bar.setFormat(f"Processing... {self.total_businesses} businesses found")
    
    def update_dashboard_keyword(self, keyword: str):
        """Update dashboard with current keyword being processed"""
        if hasattr(self, 'current_keyword_card'):
            # Find the value label in the current keyword card
            keyword_value = self.current_keyword_card.findChild(QLabel, "statValue")
            if keyword_value:
                keyword_value.setText(keyword)
            
            # Update keywords processed count
            if hasattr(self, 'scraping_thread') and self.scraping_thread:
                current_index = self.scraping_thread.keywords.index(keyword) + 1 if keyword in self.scraping_thread.keywords else 0
                total_keywords = len(self.scraping_thread.keywords)
                
                processed_value = self.keywords_processed_card.findChild(QLabel, "statValue")
                if processed_value:
                    processed_value.setText(f"{current_index}/{total_keywords}")
                
                # Update progress bar
                progress = (current_index / total_keywords) * 100 if total_keywords > 0 else 0
                self.dashboard_progress_bar.setValue(int(progress))
                self.dashboard_progress_bar.setFormat(f"Processing: {keyword}")
                
                # Update status
                status_value = self.scraping_status_card.findChild(QLabel, "statValue")
                if status_value:
                    status_value.setText("🔄 Scraping")
        
    def update_current_keyword(self, keyword: str):
        """Update the current keyword display"""
        # Removed current keyword display for cleaner interface
        pass
        
    def scraping_finished(self, result_count):
        """Handle scraping completion"""
        self.log_progress(f"🎉 Scraping completed! Total businesses found: {result_count}")
        
        # Update dashboard status to completed
        if hasattr(self, 'scraping_status_card'):
            status_value = self.scraping_status_card.findChild(QLabel, "statValue")
            if status_value:
                status_value.setText("✅ Complete")
        
        # Update progress bar to 100%
        if hasattr(self, 'dashboard_progress_bar'):
            self.dashboard_progress_bar.setValue(100)
            self.dashboard_progress_bar.setFormat(f"Completed! {result_count} businesses found")
        
        # Add completion message to dashboard activity
        if hasattr(self, 'dashboard_activity_log'):
            timestamp = time.strftime("%H:%M:%S")
            self.dashboard_activity_log.append(f"[{timestamp}] 🎉 Scraping completed! Found {result_count} businesses")
        
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
    app.setApplicationName("Solo Scrapper")
    app.setOrganizationName("SoloScrapper")
    
    # Set application icon
    app.setWindowIcon(QIcon('launchericon_rounded.png'))
    
    # Create and show the main window
    window = ModernScraperGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
