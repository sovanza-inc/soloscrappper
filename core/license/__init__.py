"""License management module for Solo Scrapper Pro.

This module handles license validation, machine binding, and local caching
of license information for the Google Maps scraper application."""

from .manager import LicenseManager
from .dialog import LicenseDialog

__all__ = ['LicenseManager', 'LicenseDialog']