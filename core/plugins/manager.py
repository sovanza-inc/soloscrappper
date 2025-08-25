"""Plugin manager for coordinating plugin lifecycle and operations."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
import logging

from .base import PluginInterface, PluginMetadata, PluginType
from .loader import PluginLoader


class PluginManager:
    """Manages plugin lifecycle, configuration, and operations."""
    
    def __init__(self, config_dir: str = None):
        """Initialize the plugin manager.
        
        Args:
            config_dir: Directory to store plugin configurations
        """
        self.logger = logging.getLogger(__name__)
        self.config_dir = config_dir or str(Path.home() / ".solo_scrapper")
        self.plugin_config_file = os.path.join(self.config_dir, "plugins.json")
        
        self.loader = PluginLoader()
        self.active_plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load plugin configurations
        self._load_plugin_configs()
    
    def _load_plugin_configs(self):
        """Load plugin configurations from file."""
        if os.path.exists(self.plugin_config_file):
            try:
                with open(self.plugin_config_file, 'r') as f:
                    self.plugin_configs = json.load(f)
                self.logger.info(f"Loaded plugin configurations from {self.plugin_config_file}")
            except Exception as e:
                self.logger.error(f"Error loading plugin configs: {str(e)}")
                self.plugin_configs = {}
        else:
            self.plugin_configs = {}
    
    def _save_plugin_configs(self):
        """Save plugin configurations to file."""
        try:
            with open(self.plugin_config_file, 'w') as f:
                json.dump(self.plugin_configs, f, indent=2)
            self.logger.info(f"Saved plugin configurations to {self.plugin_config_file}")
        except Exception as e:
            self.logger.error(f"Error saving plugin configs: {str(e)}")
    
    def initialize(self) -> bool:
        """Initialize the plugin manager and load all plugins.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Load all available plugins
            loaded_plugins = self.loader.load_all_plugins()
            self.logger.info(f"Plugin manager initialized with {len(loaded_plugins)} plugins")
            
            # Auto-enable plugins that are configured to be enabled
            self._auto_enable_plugins()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing plugin manager: {str(e)}")
            return False
    
    def _auto_enable_plugins(self):
        """Automatically enable plugins based on configuration."""
        for plugin_name, plugin_class in self.loader.get_loaded_plugins().items():
            try:
                # Get plugin metadata
                temp_instance = plugin_class()
                metadata = temp_instance.metadata
                
                # Check if plugin should be auto-enabled
                plugin_config = self.plugin_configs.get(plugin_name, {})
                auto_enable = plugin_config.get('auto_enable', metadata.enabled)
                
                if auto_enable:
                    self.enable_plugin(plugin_name, plugin_config.get('config', {}))
                    
            except Exception as e:
                self.logger.error(f"Error auto-enabling plugin {plugin_name}: {str(e)}")
    
    def enable_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """Enable a plugin with optional configuration.
        
        Args:
            plugin_name: Name of the plugin to enable
            config: Optional configuration for the plugin
            
        Returns:
            bool: True if plugin enabled successfully
        """
        if plugin_name in self.active_plugins:
            self.logger.warning(f"Plugin {plugin_name} is already enabled")
            return True
        
        try:
            # Create plugin instance
            instance = self.loader.create_plugin_instance(plugin_name, config)
            if not instance:
                return False
            
            self.active_plugins[plugin_name] = instance
            
            # Update configuration
            if plugin_name not in self.plugin_configs:
                self.plugin_configs[plugin_name] = {}
            
            self.plugin_configs[plugin_name].update({
                'enabled': True,
                'auto_enable': True,
                'config': config or {}
            })
            
            self._save_plugin_configs()
            
            self.logger.info(f"Successfully enabled plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling plugin {plugin_name}: {str(e)}")
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable an active plugin.
        
        Args:
            plugin_name: Name of the plugin to disable
            
        Returns:
            bool: True if plugin disabled successfully
        """
        if plugin_name not in self.active_plugins:
            self.logger.warning(f"Plugin {plugin_name} is not active")
            return True
        
        try:
            # Clean up plugin
            instance = self.active_plugins[plugin_name]
            instance.cleanup()
            
            # Remove from active plugins
            del self.active_plugins[plugin_name]
            
            # Update configuration
            if plugin_name in self.plugin_configs:
                self.plugin_configs[plugin_name]['enabled'] = False
                self.plugin_configs[plugin_name]['auto_enable'] = False
            
            self._save_plugin_configs()
            
            self.logger.info(f"Successfully disabled plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling plugin {plugin_name}: {str(e)}")
            return False
    
    def get_active_plugins(self) -> Dict[str, PluginInterface]:
        """Get all active plugin instances.
        
        Returns:
            Dictionary of active plugins {name: instance}
        """
        return self.active_plugins.copy()
    
    def get_available_plugins(self) -> Dict[str, Type[PluginInterface]]:
        """Get all available plugin classes.
        
        Returns:
            Dictionary of available plugins {name: class}
        """
        return self.loader.get_loaded_plugins()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary containing plugin information
        """
        plugin_class = self.loader.get_plugin_by_name(plugin_name)
        if not plugin_class:
            return None
        
        try:
            temp_instance = plugin_class()
            metadata = temp_instance.metadata
            
            return {
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'type': metadata.plugin_type.value,
                'dependencies': metadata.dependencies,
                'min_app_version': metadata.min_app_version,
                'max_app_version': metadata.max_app_version,
                'enabled': plugin_name in self.active_plugins,
                'config_schema': temp_instance.get_config_schema()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting plugin info for {plugin_name}: {str(e)}")
            return None
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """Get all active plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of active plugin instances of the specified type
        """
        matching_plugins = []
        
        for plugin_name, instance in self.active_plugins.items():
            try:
                if instance.metadata.plugin_type == plugin_type:
                    matching_plugins.append(instance)
            except Exception as e:
                self.logger.error(f"Error checking plugin type for {plugin_name}: {str(e)}")
        
        return matching_plugins
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Configure a plugin.
        
        Args:
            plugin_name: Name of the plugin to configure
            config: New configuration for the plugin
            
        Returns:
            bool: True if configuration successful
        """
        try:
            # Validate configuration if plugin is available
            plugin_class = self.loader.get_plugin_by_name(plugin_name)
            if plugin_class:
                temp_instance = plugin_class()
                if not temp_instance.validate_config(config):
                    self.logger.error(f"Invalid configuration for plugin {plugin_name}")
                    return False
            
            # Update configuration
            if plugin_name not in self.plugin_configs:
                self.plugin_configs[plugin_name] = {}
            
            self.plugin_configs[plugin_name]['config'] = config
            self._save_plugin_configs()
            
            # If plugin is active, restart it with new configuration
            if plugin_name in self.active_plugins:
                self.disable_plugin(plugin_name)
                self.enable_plugin(plugin_name, config)
            
            self.logger.info(f"Successfully configured plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring plugin {plugin_name}: {str(e)}")
            return False
    
    def reload_plugins(self) -> bool:
        """Reload all plugins.
        
        Returns:
            bool: True if reload successful
        """
        try:
            # Store currently active plugins
            active_plugin_names = list(self.active_plugins.keys())
            
            # Disable all active plugins
            for plugin_name in active_plugin_names:
                self.disable_plugin(plugin_name)
            
            # Clear loader cache
            self.loader.cleanup_all_instances()
            self.loader.loaded_plugins.clear()
            
            # Reload all plugins
            self.loader.load_all_plugins()
            
            # Re-enable previously active plugins
            for plugin_name in active_plugin_names:
                plugin_config = self.plugin_configs.get(plugin_name, {}).get('config', {})
                self.enable_plugin(plugin_name, plugin_config)
            
            self.logger.info("Successfully reloaded all plugins")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reloading plugins: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up all plugins and resources."""
        try:
            # Disable all active plugins
            for plugin_name in list(self.active_plugins.keys()):
                self.disable_plugin(plugin_name)
            
            # Clean up loader
            self.loader.cleanup_all_instances()
            
            self.logger.info("Plugin manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during plugin manager cleanup: {str(e)}")
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """Get overall plugin system status.
        
        Returns:
            Dictionary containing plugin system status
        """
        available_plugins = self.get_available_plugins()
        active_plugins = self.get_active_plugins()
        
        status = {
            'total_available': len(available_plugins),
            'total_active': len(active_plugins),
            'available_plugins': list(available_plugins.keys()),
            'active_plugins': list(active_plugins.keys()),
            'plugin_types': {}
        }
        
        # Count plugins by type
        for plugin_type in PluginType:
            type_plugins = self.get_plugins_by_type(plugin_type)
            status['plugin_types'][plugin_type.value] = len(type_plugins)
        
        return status