import sys
import os
import asyncio
import threading
import csv
import random
import time
from pathlib import Path
from typing import List, Dict, Optional
import re

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("Playwright is not installed. Please install it using:")
    print("pip install playwright")
    print("python -m playwright install")
    sys.exit(1)

try:
    from PyQt5.QtCore import QThread, pyqtSignal
except ImportError:
    print("PyQt5 is not installed. Please install it using:")
    print("pip install PyQt5")
    sys.exit(1)


class GoogleMapsScraper:
    """Google Maps scraper using Playwright for browser automation"""
    
    def __init__(self, scraping_thread=None):
        self.browser = None
        self.browser_context = None
        self.page = None
        self.scraping_thread = scraping_thread
        self.temp_profile = None
    
    async def setup_browser(self, chrome_path=None, profile_path=None, progress_callback=None):
        """Setup browser with optional Chrome path and profile"""
        try:
            if progress_callback:
                progress_callback.emit("🚀 Starting browser...")
            
            playwright = await async_playwright().start()
            
            # Browser launch options
            launch_options = {
                'headless': False,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions-except',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--window-size=1920,1080'
                ]
            }
            
            # Add Chrome executable path if provided
            if chrome_path and os.path.exists(chrome_path):
                launch_options['executable_path'] = chrome_path
                if progress_callback:
                    progress_callback.emit(f"🔧 Using Chrome: {chrome_path}")
            
            # Use a temporary profile directory to avoid conflicts
            if profile_path and os.path.exists(profile_path):
                if progress_callback:
                    progress_callback.emit(f"👤 Creating temporary profile based on: {profile_path}")
                
                # Create a temporary profile directory to avoid SingletonLock issues
                import tempfile
                import shutil
                temp_profile = tempfile.mkdtemp(prefix="chrome_profile_")
                
                # Copy essential profile data if needed (optional)
                # For now, use clean temporary profile to avoid conflicts
                
                # Remove web security disable flag that requires non-default user-data-dir
                safe_launch_options = launch_options.copy()
                safe_launch_options['args'] = [arg for arg in launch_options['args'] if not arg.startswith('--disable-web-security')]
                
                # Remove executable_path from launch_options for persistent context
                if 'executable_path' in safe_launch_options:
                    safe_launch_options['channel'] = 'chrome'  # Use system Chrome
                    del safe_launch_options['executable_path']
                
                self.browser_context = await playwright.chromium.launch_persistent_context(
                    user_data_dir=temp_profile,
                    viewport={'width': 1920, 'height': 1080},
                    **safe_launch_options
                )
                self.browser = None  # Not needed with persistent context
                self.temp_profile = temp_profile  # Store for cleanup
            else:
                self.browser = await playwright.chromium.launch(**launch_options)
                self.browser_context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.browser_context.new_page()
            
            # Set additional page properties to avoid detection
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            if progress_callback:
                progress_callback.emit("✅ Browser setup complete")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback.emit(f"❌ Browser setup failed: {str(e)}")
            return False
    
    async def search_keyword(self, keyword: str, progress_callback=None, business_callback=None) -> List[Dict[str, str]]:
        """Search for businesses using a keyword on Google Maps"""
        try:
            if progress_callback:
                progress_callback.emit(f"🔍 Searching for: {keyword}")
            
            # Navigate to Google Maps with retry mechanism
            navigation_success = False
            for attempt in range(2):
                try:
                    if attempt == 0:
                        maps_url = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}"
                    else:
                        # Fallback URL format
                        maps_url = f"https://maps.google.com/maps?q={keyword.replace(' ', '+')}"
                    
                    if progress_callback:
                        progress_callback.emit(f"🌐 Navigating to: {maps_url} (attempt {attempt + 1})")
                    
                    await self.page.goto(maps_url, wait_until='domcontentloaded', timeout=30000)
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
        """Close the browser context and browser if needed"""
        try:
            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None
            
            # Close browser if it exists (not needed for persistent context)
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            # Clean up temporary profile directory
            if hasattr(self, 'temp_profile'):
                import shutil
                try:
                    shutil.rmtree(self.temp_profile)
                except Exception as cleanup_error:
                    print(f"Warning: Could not clean up temp profile: {cleanup_error}")
                delattr(self, 'temp_profile')
                
            self.page = None
        except Exception as e:
            print(f"Error closing browser: {e}")


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
        """Main scraping execution"""
        asyncio.run(self._run_scraping())
    
    async def _run_scraping(self):
        """Async scraping execution"""
        try:
            # Setup browser
            setup_success = await self.scraper.setup_browser(
                self.chrome_path, 
                self.profile_path, 
                self.progress_signal
            )
            
            if not setup_success:
                self.finished_signal.emit(0)
                return
            
            all_businesses = []
            
            # Process each keyword
            for keyword in self.keywords:
                if not self.is_running:
                    break
                
                # Wait if paused
                while self.is_paused:
                    await asyncio.sleep(0.1)
                    if not self.is_running:
                        break
                
                if not self.is_running:
                    break
                
                self.keyword_signal.emit(keyword)
                
                # Search for businesses
                businesses = await self.scraper.search_keyword(
                    keyword, 
                    self.progress_signal, 
                    self.business_signal
                )
                
                all_businesses.extend(businesses)
            
            # Save results to CSV
            if all_businesses and self.output_file:
                self._save_to_csv(all_businesses)
            
            # Close browser
            await self.scraper.close_browser()
            
            self.finished_signal.emit(len(all_businesses))
            
        except Exception as e:
            self.progress_signal.emit(f"❌ Scraping error: {str(e)}")
            self.finished_signal.emit(0)
    
    def _save_to_csv(self, businesses):
        """Save business data to CSV file"""
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'address', 'phone', 'website', 'rating', 'reviews', 'category', 'keyword']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for business in businesses:
                    writer.writerow(business)
                    
            self.progress_signal.emit(f"✅ Saved {len(businesses)} businesses to {self.output_file}")
            
        except Exception as e:
            self.progress_signal.emit(f"❌ Error saving CSV: {str(e)}")