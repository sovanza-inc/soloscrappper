"""Plugin loader for discovering and loading plugins."""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Type, Optional, Any
import logging

from .base import PluginInterface, PluginMetadata, PluginType


class PluginLoader:
    """Handles plugin discovery and loading."""
    
    def __init__(self, plugin_directories: List[str] = None):
        """Initialize the plugin loader.
        
        Args:
            plugin_directories: List of directories to search for plugins
        """
        self.logger = logging.getLogger(__name__)
        self.plugin_directories = plugin_directories or []
        self.loaded_plugins: Dict[str, Type[PluginInterface]] = {}
        self.plugin_instances: Dict[str, PluginInterface] = {}
        
        # Add default plugin directories
        self._add_default_directories()
    
    def _add_default_directories(self):
        """Add default plugin directories."""
        # Add plugins directory relative to the application
        app_dir = Path(__file__).parent.parent.parent
        default_dirs = [
            str(app_dir / "plugins"),
            str(Path.home() / ".solo_scrapper" / "plugins"),
        ]
        
        for directory in default_dirs:
            if directory not in self.plugin_directories:
                self.plugin_directories.append(directory)
    
    def discover_plugins(self) -> List[str]:
        """Discover all available plugins.
        
        Returns:
            List of plugin file paths
        """
        plugin_files = []
        
        for directory in self.plugin_directories:
            if not os.path.exists(directory):
                continue
                
            self.logger.info(f"Searching for plugins in: {directory}")
            
            for root, dirs, files in os.walk(directory):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('_'):
                        plugin_path = os.path.join(root, file)
                        plugin_files.append(plugin_path)
                        self.logger.debug(f"Found potential plugin: {plugin_path}")
        
        return plugin_files
    
    def load_plugin(self, plugin_path: str) -> Optional[Type[PluginInterface]]:
        """Load a single plugin from file path.
        
        Args:
            plugin_path: Path to the plugin file
            
        Returns:
            Plugin class if loaded successfully, None otherwise
        """
        try:
            # Get module name from file path
            module_name = Path(plugin_path).stem
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                self.logger.error(f"Could not load spec for plugin: {plugin_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes in the module
            plugin_classes = self._find_plugin_classes(module)
            
            if not plugin_classes:
                self.logger.warning(f"No plugin classes found in: {plugin_path}")
                return None
            
            if len(plugin_classes) > 1:
                self.logger.warning(f"Multiple plugin classes found in {plugin_path}, using first one")
            
            plugin_class = plugin_classes[0]
            plugin_name = plugin_class.__name__
            
            # Validate plugin
            if not self._validate_plugin_class(plugin_class):
                self.logger.error(f"Plugin validation failed: {plugin_name}")
                return None
            
            self.loaded_plugins[plugin_name] = plugin_class
            self.logger.info(f"Successfully loaded plugin: {plugin_name}")
            
            return plugin_class
            
        except Exception as e:
            self.logger.error(f"Error loading plugin from {plugin_path}: {str(e)}")
            return None
    
    def _find_plugin_classes(self, module) -> List[Type[PluginInterface]]:
        """Find plugin classes in a module.
        
        Args:
            module: Python module to search
            
        Returns:
            List of plugin classes found
        """
        plugin_classes = []
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            if (isinstance(attr, type) and 
                issubclass(attr, PluginInterface) and 
                attr != PluginInterface):
                plugin_classes.append(attr)
        
        return plugin_classes
    
    def _validate_plugin_class(self, plugin_class: Type[PluginInterface]) -> bool:
        """Validate a plugin class.
        
        Args:
            plugin_class: Plugin class to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Try to create an instance to check if it's properly implemented
            instance = plugin_class()
            
            # Check if required methods are implemented
            required_methods = ['metadata', 'initialize', 'cleanup']
            for method in required_methods:
                if not hasattr(instance, method):
                    self.logger.error(f"Plugin {plugin_class.__name__} missing required method: {method}")
                    return False
            
            # Try to get metadata
            metadata = instance.metadata
            if not isinstance(metadata, PluginMetadata):
                self.logger.error(f"Plugin {plugin_class.__name__} metadata is not PluginMetadata instance")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating plugin {plugin_class.__name__}: {str(e)}")
            return False
    
    def load_all_plugins(self) -> Dict[str, Type[PluginInterface]]:
        """Load all discovered plugins.
        
        Returns:
            Dictionary of loaded plugins {name: class}
        """
        plugin_files = self.discover_plugins()
        
        self.logger.info(f"Found {len(plugin_files)} potential plugin files")
        
        for plugin_file in plugin_files:
            self.load_plugin(plugin_file)
        
        self.logger.info(f"Successfully loaded {len(self.loaded_plugins)} plugins")
        
        return self.loaded_plugins.copy()
    
    def get_loaded_plugins(self) -> Dict[str, Type[PluginInterface]]:
        """Get all loaded plugin classes.
        
        Returns:
            Dictionary of loaded plugins {name: class}
        """
        return self.loaded_plugins.copy()
    
    def get_plugin_by_name(self, name: str) -> Optional[Type[PluginInterface]]:
        """Get a plugin class by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class if found, None otherwise
        """
        return self.loaded_plugins.get(name)
    
    def create_plugin_instance(self, name: str, config: Dict[str, Any] = None) -> Optional[PluginInterface]:
        """Create an instance of a plugin.
        
        Args:
            name: Plugin name
            config: Optional configuration for the plugin
            
        Returns:
            Plugin instance if successful, None otherwise
        """
        plugin_class = self.get_plugin_by_name(name)
        if not plugin_class:
            self.logger.error(f"Plugin not found: {name}")
            return None
        
        try:
            instance = plugin_class()
            
            # Initialize the plugin
            if not instance.initialize(config or {}):
                self.logger.error(f"Failed to initialize plugin: {name}")
                return None
            
            self.plugin_instances[name] = instance
            return instance
            
        except Exception as e:
            self.logger.error(f"Error creating plugin instance {name}: {str(e)}")
            return None
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Type[PluginInterface]]:
        """Get all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugin classes of the specified type
        """
        matching_plugins = []
        
        for plugin_class in self.loaded_plugins.values():
            try:
                instance = plugin_class()
                if instance.metadata.plugin_type == plugin_type:
                    matching_plugins.append(plugin_class)
            except Exception as e:
                self.logger.error(f"Error checking plugin type for {plugin_class.__name__}: {str(e)}")
        
        return matching_plugins
    
    def cleanup_all_instances(self):
        """Clean up all plugin instances."""
        for name, instance in self.plugin_instances.items():
            try:
                instance.cleanup()
                self.logger.info(f"Cleaned up plugin instance: {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up plugin {name}: {str(e)}")
        
        self.plugin_instances.clear()