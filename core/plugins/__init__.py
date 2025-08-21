"""Plugin system for Solo Scrapper."""

from .base import PluginInterface, PluginMetadata
from .loader import PluginLoader
from .manager import PluginManager

__all__ = ['PluginInterface', 'PluginMetadata', 'PluginLoader', 'PluginManager']