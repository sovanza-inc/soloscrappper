"""Utility functions and helpers for the Google Maps Scraper application.

This module provides common utility functions including:
- Location data loading and processing
- Keyword generation and variations
- File operations and path utilities
- System information helpers
"""

import os
import sys
import hashlib
import uuid
import platform
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime


class LocationDataLoader:
    """Handler for loading and processing location data"""
    
    def __init__(self, locations_file: str = 'global_locations.json'):
        """Initialize location data loader
        
        Args:
            locations_file: Path to the locations file
        """
        self.locations_file = locations_file
        self.location_data = {}
        self.load_location_data()
    
    def load_location_data(self) -> Dict[str, Dict[str, List[str]]]:
        """Load location data from JSON file
        
        Returns:
            Dictionary mapping countries to states to lists of cities
        """
        self.location_data = {}
        
        try:
            locations_path = Path(self.locations_file)
            if not locations_path.exists():
                print(f"Warning: {self.locations_file} file not found!")
                # Fallback data
                self.location_data = {
                    "United States": {
                        "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
                        "New York": ["New York City", "Buffalo", "Rochester", "Syracuse"],
                        "Texas": ["Houston", "Dallas", "Austin", "San Antonio"]
                    },
                    "Canada": {
                        "Ontario": ["Toronto", "Ottawa", "Hamilton", "London"],
                        "Quebec": ["Montreal", "Quebec City", "Laval", "Gatineau"]
                    }
                }
                return self.location_data
                
            with open(locations_path, 'r', encoding='utf-8') as file:
                self.location_data = json.load(file)
                        
            print(f"Loaded {len(self.location_data)} countries with location data")
            
        except Exception as e:
            print(f"Error loading location data: {e}")
            # Fallback data
            self.location_data = {
                "United States": {
                    "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
                    "New York": ["New York City", "Buffalo", "Rochester", "Syracuse"],
                    "Texas": ["Houston", "Dallas", "Austin", "San Antonio"]
                },
                "Canada": {
                    "Ontario": ["Toronto", "Ottawa", "Hamilton", "London"],
                    "Quebec": ["Montreal", "Quebec City", "Laval", "Gatineau"]
                }
            }
            
        return self.location_data
    
    def get_countries(self) -> List[str]:
        """Get list of available countries
        
        Returns:
            List of country names
        """
        return list(self.location_data.keys())
    
    def get_states(self, country: str = None) -> List[str]:
        """Get list of available states
        
        Args:
            country: Country name (if None, returns all states from all countries)
        
        Returns:
            List of state names
        """
        if country:
            return list(self.location_data.get(country, {}).keys())
        
        all_states = []
        for country_data in self.location_data.values():
            all_states.extend(country_data.keys())
        return all_states
    
    def get_cities_for_state(self, state: str, country: str = None) -> List[str]:
        """Get list of cities for a specific state
        
        Args:
            state: State name
            country: Country name (if None, searches all countries)
            
        Returns:
            List of city names
        """
        if country:
            return self.location_data.get(country, {}).get(state, [])
        
        # Search all countries for the state
        for country_data in self.location_data.values():
            if state in country_data:
                return country_data[state]
        return []
    
    def get_location_data(self) -> Dict[str, Dict[str, List[str]]]:
        """Get the complete location data dictionary
        
        Returns:
            Dictionary mapping countries to states to lists of cities
        """
        return self.location_data
    
    def get_all_cities(self) -> List[str]:
        """Get list of all cities from all countries and states
        
        Returns:
            List of all city names
        """
        all_cities = []
        for country_data in self.location_data.values():
            for cities in country_data.values():
                all_cities.extend(cities)
        return sorted(set(all_cities))
    
    def search_locations(self, query: str) -> Dict[str, List[str]]:
        """Search for locations matching a query
        
        Args:
            query: Search query
            
        Returns:
            Dictionary of matching countries, states and cities
        """
        query_lower = query.lower()
        results = {'countries': [], 'states': [], 'cities': []}
        
        # Search countries
        for country in self.location_data.keys():
            if query_lower in country.lower():
                results['countries'].append(country)
        
        # Search states and cities
        for country, country_data in self.location_data.items():
            for state, cities in country_data.items():
                if query_lower in state.lower():
                    results['states'].append(f"{state}, {country}")
                
                for city in cities:
                    if query_lower in city.lower():
                        results['cities'].append(f"{city}, {state}, {country}")
        
        return results


class KeywordGenerator:
    """Generator for keyword variations"""
    
    @staticmethod
    def generate_variations(base_keyword: str, locations: List[str]) -> List[str]:
        """Generate keyword variations with locations
        
        Args:
            base_keyword: Base keyword to generate variations for
            locations: List of location modifiers
            
        Returns:
            List of keyword variations
        """
        if not base_keyword.strip():
            return []
            
        variations = []
        
        # Base keyword + location modifiers (only "in" format)
        for location in locations:
            if location.strip():
                variations.append(f"{base_keyword.strip()} in {location.strip()}")
        
        # Remove duplicates while preserving order
        unique_variations = []
        seen = set()
        for var in variations:
            var_lower = var.lower()
            if var_lower not in seen:
                unique_variations.append(var)
                seen.add(var_lower)
        
        return unique_variations
    
    @staticmethod
    def generate_business_type_variations(base_keyword: str) -> List[str]:
        """Generate variations with common business type modifiers
        
        Args:
            base_keyword: Base keyword
            
        Returns:
            List of business type variations
        """
        if not base_keyword.strip():
            return []
            
        modifiers = [
            'best', 'top', 'local', 'nearby', 'professional', 'affordable',
            'quality', 'trusted', 'experienced', 'reliable', 'recommended'
        ]
        
        suffixes = [
            'services', 'company', 'business', 'shop', 'store', 'center',
            'near me', 'in my area', 'reviews', 'ratings'
        ]
        
        variations = [base_keyword.strip()]
        
        # Add modifier variations
        for modifier in modifiers:
            variations.append(f"{modifier} {base_keyword.strip()}")
        
        # Add suffix variations
        for suffix in suffixes:
            variations.append(f"{base_keyword.strip()} {suffix}")
        
        # Remove duplicates
        return list(dict.fromkeys(variations))
    
    @staticmethod
    def expand_keyword_list(keywords: List[str], max_variations: int = 50) -> List[str]:
        """Expand a list of keywords with common variations
        
        Args:
            keywords: List of base keywords
            max_variations: Maximum number of variations to generate
            
        Returns:
            Expanded list of keywords
        """
        expanded = []
        
        for keyword in keywords:
            if not keyword.strip():
                continue
                
            # Add original keyword
            expanded.append(keyword.strip())
            
            # Add common variations
            variations = [
                f"{keyword.strip()} near me",
                f"{keyword.strip()} reviews",
                f"best {keyword.strip()}",
                f"top {keyword.strip()}",
                f"local {keyword.strip()}"
            ]
            
            expanded.extend(variations)
            
            # Stop if we've reached the maximum
            if len(expanded) >= max_variations:
                break
        
        # Remove duplicates and limit to max_variations
        unique_expanded = list(dict.fromkeys(expanded))
        return unique_expanded[:max_variations]


class SystemInfo:
    """System information utilities"""
    
    @staticmethod
    def get_machine_id() -> str:
        """Generate a unique machine identifier
        
        Returns:
            Unique machine ID string
        """
        try:
            # Get system information
            system_info = {
                'platform': platform.system(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'node': platform.node()
            }
            
            # Try to get MAC address
            try:
                import uuid
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0, 2*6, 2)][::-1])
                system_info['mac'] = mac
            except:
                pass
            
            # Create hash from system info
            info_string = ''.join(str(v) for v in system_info.values())
            machine_id = hashlib.sha256(info_string.encode()).hexdigest()[:16]
            
            return machine_id.upper()
            
        except Exception as e:
            print(f"Error generating machine ID: {e}")
            # Fallback to random ID
            return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()
    
    @staticmethod
    def get_default_chrome_path() -> str:
        """Get default Chrome browser path for the current OS
        
        Returns:
            Path to Chrome executable
        """
        system = platform.system().lower()
        
        if system == 'darwin':  # macOS
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif system == 'windows':
            # Common Windows paths
            paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
            return paths[0]  # Return first path as default
        else:  # Linux
            paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
            return paths[0]  # Return first path as default
    
    @staticmethod
    def get_default_chrome_profile_path() -> str:
        """Get default Chrome profile path for the current OS
        
        Returns:
            Path to Chrome profile directory
        """
        system = platform.system().lower()
        home = Path.home()
        
        if system == 'darwin':  # macOS
            return str(home / "Library/Application Support/Google/Chrome")
        elif system == 'windows':
            return str(home / "AppData/Local/Google/Chrome/User Data")
        else:  # Linux
            return str(home / ".config/google-chrome")
    
    @staticmethod
    def get_desktop_path() -> str:
        """Get desktop path for the current user
        
        Returns:
            Path to desktop directory
        """
        return str(Path.home() / "Desktop")
    
    @staticmethod
    def get_app_data_dir() -> Path:
        """Get application data directory
        
        Returns:
            Path to application data directory
        """
        system = platform.system().lower()
        home = Path.home()
        
        if system == 'darwin':  # macOS
            app_dir = home / "Library/Application Support/GoogleMapsScraper"
        elif system == 'windows':
            app_dir = home / "AppData/Local/GoogleMapsScraper"
        else:  # Linux
            app_dir = home / ".config/GoogleMapsScraper"
        
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir


class FileUtils:
    """File operation utilities"""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Ensure directory exists, create if it doesn't
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get a safe filename by removing invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        import re
        # Remove invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        # Remove leading/trailing underscores
        safe_name = safe_name.strip('_')
        return safe_name or 'untitled'
    
    @staticmethod
    def get_unique_filename(base_path: str, extension: str = '') -> str:
        """Get a unique filename by adding numbers if file exists
        
        Args:
            base_path: Base file path without extension
            extension: File extension (with or without dot)
            
        Returns:
            Unique file path
        """
        if extension and not extension.startswith('.'):
            extension = '.' + extension
            
        counter = 1
        original_path = base_path + extension
        
        if not os.path.exists(original_path):
            return original_path
        
        while True:
            new_path = f"{base_path}_{counter}{extension}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    @staticmethod
    def read_keywords_file(file_path: str) -> List[str]:
        """Read keywords from a text file
        
        Args:
            file_path: Path to keywords file
            
        Returns:
            List of keywords
        """
        keywords = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    keyword = line.strip()
                    if keyword and not keyword.startswith('#'):
                        keywords.append(keyword)
        except Exception as e:
            print(f"Error reading keywords file {file_path}: {e}")
            
        return keywords
    
    @staticmethod
    def write_keywords_file(file_path: str, keywords: List[str]) -> bool:
        """Write keywords to a text file
        
        Args:
            file_path: Path to keywords file
            keywords: List of keywords to write
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for keyword in keywords:
                    if keyword.strip():
                        file.write(keyword.strip() + '\n')
            return True
        except Exception as e:
            print(f"Error writing keywords file {file_path}: {e}")
            return False


class TimeUtils:
    """Time and date utilities"""
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp string
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def get_time_string() -> str:
        """Get current time string (HH:MM:SS)
        
        Returns:
            Formatted time string
        """
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def get_date_string() -> str:
        """Get current date string (YYYY-MM-DD)
        
        Returns:
            Formatted date string
        """
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human readable string
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def get_session_id() -> str:
        """Generate a unique session ID
        
        Returns:
            Unique session ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_part = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{random_part}"


class ValidationUtils:
    """Data validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email address is valid
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Check if phone number is valid
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid phone number
        """
        import re
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it has 10-15 digits (international format)
        return 10 <= len(digits_only) <= 15
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid URL
        """
        import re
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text by removing extra whitespace and special characters
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Remove extra whitespace
        cleaned = ' '.join(text.split())
        
        # Remove control characters
        import re
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def validate_keyword(keyword: str) -> Tuple[bool, str]:
        """Validate a search keyword
        
        Args:
            keyword: Keyword to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not keyword or not keyword.strip():
            return False, "Keyword cannot be empty"
        
        keyword = keyword.strip()
        
        if len(keyword) < 2:
            return False, "Keyword must be at least 2 characters long"
        
        if len(keyword) > 100:
            return False, "Keyword must be less than 100 characters"
        
        # Check for invalid characters
        import re
        if re.search(r'[<>"\\]', keyword):
            return False, "Keyword contains invalid characters"
        
        return True, ""