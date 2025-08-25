"""Configuration manager for Solo Scrapper Pro.

Handles loading, saving, and managing application configuration settings.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages application configuration settings"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_dir: Custom configuration directory path
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to user's home directory
            self.config_dir = Path.home() / '.solo_scrapper'
        
        self.config_file = self.config_dir / 'config.json'
        self.ensure_config_dir()
        self._config = self.load_config()
    
    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file
        
        Returns:
            Dictionary containing configuration settings
        """
        if not self.config_file.exists():
            return self.get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            default_config = self.get_default_config()
            return self._merge_configs(default_config, config)
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}. Using defaults.")
            return self.get_default_config()
    
    def save_config(self) -> bool:
        """Save current configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings
        
        Returns:
            Dictionary with default configuration
        """
        return {
            'app': {
                'theme': 'dark',
                'language': 'en',
                'auto_save': True,
                'save_interval': 300,  # seconds
                'window_geometry': {
                    'width': 1200,
                    'height': 800,
                    'x': 100,
                    'y': 100
                }
            },
            'scraping': {
                'default_delay': 2,
                'max_retries': 3,
                'timeout': 30,
                'headless': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'max_concurrent': 1,
                'save_screenshots': False
            },
            'export': {
                'default_format': 'csv',
                'include_duplicates': False,
                'output_directory': str(Path.home() / 'Downloads' / 'SoloScrapper'),
                'filename_template': 'scraped_data_{timestamp}',
                'auto_export': False
            },
            'license': {
                'check_interval': 300,  # seconds
                'cache_duration': 86400,  # 24 hours in seconds
                'auto_validate': True
            },
            'ui': {
                'show_tooltips': True,
                'animation_enabled': True,
                'compact_mode': False,
                'show_progress_details': True,
                'remember_tab': True,
                'last_active_tab': 0
            },
            'modules': {
                'enabled_modules': [
                    'core.scraping',
                    'core.ui',
                    'core.license',
                    'core.database',
                    'core.utils'
                ],
                'module_settings': {}
            }
        }
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults
        
        Args:
            default: Default configuration
            user: User configuration
            
        Returns:
            Merged configuration
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'app.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Set configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'app.theme')
            value: Value to set
            save: Whether to save to file immediately
            
        Returns:
            True if successful, False otherwise
        """
        keys = key.split('.')
        config = self._config
        
        try:
            # Navigate to parent of target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            if save:
                return self.save_config()
            return True
            
        except (KeyError, TypeError) as e:
            print(f"Error setting config key '{key}': {e}")
            return False
    
    def delete(self, key: str, save: bool = True) -> bool:
        """Delete configuration key
        
        Args:
            key: Configuration key to delete
            save: Whether to save to file immediately
            
        Returns:
            True if successful, False otherwise
        """
        keys = key.split('.')
        config = self._config
        
        try:
            # Navigate to parent of target key
            for k in keys[:-1]:
                config = config[k]
            
            # Delete the key
            if keys[-1] in config:
                del config[keys[-1]]
                
                if save:
                    return self.save_config()
                return True
            return False
            
        except (KeyError, TypeError) as e:
            print(f"Error deleting config key '{key}': {e}")
            return False
    
    def reset_to_defaults(self, save: bool = True) -> bool:
        """Reset configuration to defaults
        
        Args:
            save: Whether to save to file immediately
            
        Returns:
            True if successful, False otherwise
        """
        self._config = self.get_default_config()
        
        if save:
            return self.save_config()
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration settings
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
    
    def update_batch(self, updates: Dict[str, Any], save: bool = True) -> bool:
        """Update multiple configuration values
        
        Args:
            updates: Dictionary of key-value pairs to update
            save: Whether to save to file immediately
            
        Returns:
            True if all updates successful, False otherwise
        """
        success = True
        
        for key, value in updates.items():
            if not self.set(key, value, save=False):
                success = False
        
        if save and success:
            return self.save_config()
        
        return success
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to file
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str, merge: bool = True) -> bool:
        """Import configuration from file
        
        Args:
            file_path: Path to import file
            merge: Whether to merge with existing config or replace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            if merge:
                self._config = self._merge_configs(self._config, imported_config)
            else:
                self._config = imported_config
            
            return self.save_config()
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing config: {e}")
            return False