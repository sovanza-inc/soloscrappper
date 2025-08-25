"""Base plugin interface and metadata classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class PluginType(Enum):
    """Types of plugins supported by the system."""
    SCRAPER = "scraper"
    DATA_PROCESSOR = "data_processor"
    EXPORTER = "exporter"
    UI_COMPONENT = "ui_component"
    UTILITY = "utility"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    min_app_version: str = "1.0.0"
    max_app_version: str = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginInterface(ABC):
    """Base interface that all plugins must implement."""
    
    def __init__(self):
        self._metadata: Optional[PluginMetadata] = None
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the plugin with optional configuration.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this plugin.
        
        Returns:
            Dict describing the expected configuration format
        """
        return {}
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if configuration is valid
        """
        return True


class ScraperPlugin(PluginInterface):
    """Base class for scraper plugins."""
    
    @abstractmethod
    def scrape(self, url: str, **kwargs) -> Dict[str, Any]:
        """Scrape data from the given URL.
        
        Args:
            url: URL to scrape
            **kwargs: Additional scraping parameters
            
        Returns:
            Dict containing scraped data
        """
        pass
    
    @abstractmethod
    def get_supported_domains(self) -> List[str]:
        """Return list of supported domains.
        
        Returns:
            List of domain patterns this scraper supports
        """
        pass


class DataProcessorPlugin(PluginInterface):
    """Base class for data processing plugins."""
    
    @abstractmethod
    def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process the given data.
        
        Args:
            data: Data to process
            **kwargs: Additional processing parameters
            
        Returns:
            Dict containing processed data
        """
        pass


class ExporterPlugin(PluginInterface):
    """Base class for data export plugins."""
    
    @abstractmethod
    def export(self, data: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """Export data to the specified path.
        
        Args:
            data: Data to export
            output_path: Path where to save the exported data
            **kwargs: Additional export parameters
            
        Returns:
            bool: True if export successful
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported export formats.
        
        Returns:
            List of file extensions this exporter supports
        """
        pass