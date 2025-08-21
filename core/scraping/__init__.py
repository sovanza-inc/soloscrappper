"""Google Maps Scraping Engine Module

This module provides the core scraping functionality for Google Maps business data extraction.
It includes the main scraper class and threading support for non-blocking operations.
"""

from .engine import GoogleMapsScraper, ScrapingThread

__all__ = ['GoogleMapsScraper', 'ScrapingThread']