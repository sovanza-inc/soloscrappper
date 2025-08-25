"""Database handler module for the Google Maps Scraper application.

This module provides centralized database operations including:
- CSV file operations for saving and loading business data
- Database connection management
- Data validation and formatting
"""

import csv
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


class CSVHandler:
    """Handler for CSV file operations"""
    
    @staticmethod
    def save_businesses_to_csv(businesses: List[Dict[str, Any]], file_path: str) -> bool:
        """Save business data to CSV file
        
        Args:
            businesses: List of business dictionaries
            file_path: Path to save the CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['keyword', 'name', 'address', 'phone', 'website', 'rating', 'reviews', 'category']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for business in businesses:
                    # Ensure all required fields exist
                    row = {field: business.get(field, '') for field in fieldnames}
                    writer.writerow(row)
                    
            return True
            
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False
    
    @staticmethod
    def load_businesses_from_csv(file_path: str) -> List[Dict[str, Any]]:
        """Load business data from CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of business dictionaries
        """
        businesses = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    businesses.append(dict(row))
                    
        except Exception as e:
            print(f"Error loading CSV: {e}")
            
        return businesses
    
    @staticmethod
    def get_unique_businesses(businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicate businesses based on name and address
        
        Args:
            businesses: List of business dictionaries
            
        Returns:
            List of unique business dictionaries
        """
        seen = set()
        unique_businesses = []
        
        for business in businesses:
            # Create a key based on name and address (case-insensitive)
            key = (
                business.get('name', '').lower().strip(),
                business.get('address', '').lower().strip()
            )
            
            # Skip empty entries and duplicates
            if key != ('', '') and key not in seen:
                seen.add(key)
                unique_businesses.append(business)
                
        return unique_businesses


class LocalDatabase:
    """Local SQLite database handler for caching and storage"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database handler
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = str(Path.home() / '.google_maps_scraper' / 'cache.db')
            
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create businesses cache table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS businesses_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        name TEXT NOT NULL,
                        address TEXT,
                        phone TEXT,
                        website TEXT,
                        rating TEXT,
                        reviews TEXT,
                        category TEXT,
                        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(keyword, name, address)
                    )
                ''')
                
                # Create scraping sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scraping_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        keywords TEXT NOT NULL,
                        total_businesses INTEGER DEFAULT 0,
                        unique_businesses INTEGER DEFAULT 0,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        status TEXT DEFAULT 'running'
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def cache_business(self, business: Dict[str, Any]) -> bool:
        """Cache a business in the local database
        
        Args:
            business: Business dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO businesses_cache 
                    (keyword, name, address, phone, website, rating, reviews, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    business.get('keyword', ''),
                    business.get('name', ''),
                    business.get('address', ''),
                    business.get('phone', ''),
                    business.get('website', ''),
                    business.get('rating', ''),
                    business.get('reviews', ''),
                    business.get('category', '')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error caching business: {e}")
            return False
    
    def get_cached_businesses(self, keyword: str) -> List[Dict[str, Any]]:
        """Get cached businesses for a keyword
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of cached business dictionaries
        """
        businesses = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT keyword, name, address, phone, website, rating, reviews, category
                    FROM businesses_cache 
                    WHERE keyword = ?
                    ORDER BY scraped_at DESC
                ''', (keyword,))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    businesses.append({
                        'keyword': row[0],
                        'name': row[1],
                        'address': row[2],
                        'phone': row[3],
                        'website': row[4],
                        'rating': row[5],
                        'reviews': row[6],
                        'category': row[7]
                    })
                    
        except Exception as e:
            print(f"Error retrieving cached businesses: {e}")
            
        return businesses
    
    def create_session(self, session_id: str, keywords: List[str]) -> bool:
        """Create a new scraping session
        
        Args:
            session_id: Unique session identifier
            keywords: List of keywords to scrape
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO scraping_sessions (session_id, keywords)
                    VALUES (?, ?)
                ''', (session_id, json.dumps(keywords)))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def update_session_stats(self, session_id: str, total_businesses: int, unique_businesses: int) -> bool:
        """Update session statistics
        
        Args:
            session_id: Session identifier
            total_businesses: Total number of businesses found
            unique_businesses: Number of unique businesses
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE scraping_sessions 
                    SET total_businesses = ?, unique_businesses = ?
                    WHERE session_id = ?
                ''', (total_businesses, unique_businesses, session_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating session stats: {e}")
            return False
    
    def complete_session(self, session_id: str) -> bool:
        """Mark a session as completed
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE scraping_sessions 
                    SET completed_at = CURRENT_TIMESTAMP, status = 'completed'
                    WHERE session_id = ?
                ''', (session_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error completing session: {e}")
            return False
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scraping session history
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        sessions = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT session_id, keywords, total_businesses, unique_businesses, 
                           started_at, completed_at, status
                    FROM scraping_sessions 
                    ORDER BY started_at DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    sessions.append({
                        'session_id': row[0],
                        'keywords': json.loads(row[1]) if row[1] else [],
                        'total_businesses': row[2],
                        'unique_businesses': row[3],
                        'started_at': row[4],
                        'completed_at': row[5],
                        'status': row[6]
                    })
                    
        except Exception as e:
            print(f"Error retrieving session history: {e}")
            
        return sessions


class DataValidator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_business_data(business: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean business data
        
        Args:
            business: Raw business dictionary
            
        Returns:
            Cleaned business dictionary
        """
        cleaned = {}
        
        # Required fields with defaults
        required_fields = {
            'keyword': '',
            'name': '',
            'address': '',
            'phone': '',
            'website': '',
            'rating': '',
            'reviews': '',
            'category': ''
        }
        
        for field, default in required_fields.items():
            value = business.get(field, default)
            
            # Clean and validate the value
            if isinstance(value, str):
                value = value.strip()
                
                # Special cleaning for specific fields
                if field == 'phone':
                    value = DataValidator._clean_phone_number(value)
                elif field == 'website':
                    value = DataValidator._clean_website_url(value)
                elif field == 'rating':
                    value = DataValidator._clean_rating(value)
                    
            cleaned[field] = value
            
        return cleaned
    
    @staticmethod
    def _clean_phone_number(phone: str) -> str:
        """Clean and format phone number"""
        if not phone:
            return ''
            
        # Remove common prefixes and clean
        phone = phone.replace('tel:', '').replace('phone:', '').strip()
        
        # Keep only digits, spaces, hyphens, parentheses, and plus signs
        import re
        phone = re.sub(r'[^\d\s\-\(\)\+]', '', phone)
        
        return phone.strip()
    
    @staticmethod
    def _clean_website_url(url: str) -> str:
        """Clean and format website URL"""
        if not url:
            return ''
            
        url = url.strip()
        
        # Add protocol if missing
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
    
    @staticmethod
    def _clean_rating(rating: str) -> str:
        """Clean and format rating"""
        if not rating:
            return ''
            
        # Extract numeric rating
        import re
        match = re.search(r'(\d+\.?\d*)', rating)
        if match:
            return match.group(1)
            
        return rating.strip()