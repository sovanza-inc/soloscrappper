"""Configuration management module for Solo Scrapper Pro.

This module handles application settings, module configuration,
and persistent storage of user preferences.
"""

from .manager import ConfigManager
from .settings import AppSettings

__all__ = ['ConfigManager', 'AppSettings']