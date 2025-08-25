"""Application settings management for Solo Scrapper Pro.

Provides a high-level interface for managing application settings
with validation and type safety.
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from .manager import ConfigManager


class AppSettings:
    """High-level application settings manager with validation"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize application settings
        
        Args:
            config_manager: Optional ConfigManager instance
        """
        self.config = config_manager or ConfigManager()
    
    # App Settings
    @property
    def theme(self) -> str:
        """Get current theme"""
        return self.config.get('app.theme', 'dark')
    
    @theme.setter
    def theme(self, value: str):
        """Set theme with validation"""
        if value not in ['dark', 'light']:
            raise ValueError("Theme must be 'dark' or 'light'")
        self.config.set('app.theme', value)
    
    @property
    def language(self) -> str:
        """Get current language"""
        return self.config.get('app.language', 'en')
    
    @language.setter
    def language(self, value: str):
        """Set language"""
        self.config.set('app.language', value)
    
    @property
    def auto_save(self) -> bool:
        """Get auto-save setting"""
        return self.config.get('app.auto_save', True)
    
    @auto_save.setter
    def auto_save(self, value: bool):
        """Set auto-save setting"""
        self.config.set('app.auto_save', bool(value))
    
    @property
    def save_interval(self) -> int:
        """Get auto-save interval in seconds"""
        return self.config.get('app.save_interval', 300)
    
    @save_interval.setter
    def save_interval(self, value: int):
        """Set auto-save interval with validation"""
        if value < 30:
            raise ValueError("Save interval must be at least 30 seconds")
        self.config.set('app.save_interval', int(value))
    
    # Window Settings
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry settings"""
        return self.config.get('app.window_geometry', {
            'width': 1200,
            'height': 800,
            'x': 100,
            'y': 100
        })
    
    def set_window_geometry(self, width: int, height: int, x: int, y: int):
        """Set window geometry"""
        geometry = {
            'width': max(800, int(width)),
            'height': max(600, int(height)),
            'x': max(0, int(x)),
            'y': max(0, int(y))
        }
        self.config.set('app.window_geometry', geometry)
    
    # Scraping Settings
    @property
    def scraping_delay(self) -> float:
        """Get scraping delay in seconds"""
        return self.config.get('scraping.default_delay', 2.0)
    
    @scraping_delay.setter
    def scraping_delay(self, value: float):
        """Set scraping delay with validation"""
        if value < 0.5:
            raise ValueError("Scraping delay must be at least 0.5 seconds")
        self.config.set('scraping.default_delay', float(value))
    
    @property
    def max_retries(self) -> int:
        """Get maximum retry attempts"""
        return self.config.get('scraping.max_retries', 3)
    
    @max_retries.setter
    def max_retries(self, value: int):
        """Set maximum retries with validation"""
        if value < 0 or value > 10:
            raise ValueError("Max retries must be between 0 and 10")
        self.config.set('scraping.max_retries', int(value))
    
    @property
    def scraping_timeout(self) -> int:
        """Get scraping timeout in seconds"""
        return self.config.get('scraping.timeout', 30)
    
    @scraping_timeout.setter
    def scraping_timeout(self, value: int):
        """Set scraping timeout with validation"""
        if value < 10 or value > 300:
            raise ValueError("Timeout must be between 10 and 300 seconds")
        self.config.set('scraping.timeout', int(value))
    
    @property
    def headless_mode(self) -> bool:
        """Get headless browser mode setting"""
        return self.config.get('scraping.headless', True)
    
    @headless_mode.setter
    def headless_mode(self, value: bool):
        """Set headless browser mode"""
        self.config.set('scraping.headless', bool(value))
    
    @property
    def user_agent(self) -> str:
        """Get user agent string"""
        return self.config.get('scraping.user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    @user_agent.setter
    def user_agent(self, value: str):
        """Set user agent string"""
        if not value.strip():
            raise ValueError("User agent cannot be empty")
        self.config.set('scraping.user_agent', value.strip())
    
    @property
    def save_screenshots(self) -> bool:
        """Get screenshot saving setting"""
        return self.config.get('scraping.save_screenshots', False)
    
    @save_screenshots.setter
    def save_screenshots(self, value: bool):
        """Set screenshot saving"""
        self.config.set('scraping.save_screenshots', bool(value))
    
    # Export Settings
    @property
    def default_export_format(self) -> str:
        """Get default export format"""
        return self.config.get('export.default_format', 'csv')
    
    @default_export_format.setter
    def default_export_format(self, value: str):
        """Set default export format with validation"""
        if value not in ['csv', 'json', 'xlsx']:
            raise ValueError("Export format must be 'csv', 'json', or 'xlsx'")
        self.config.set('export.default_format', value)
    
    @property
    def include_duplicates(self) -> bool:
        """Get include duplicates setting"""
        return self.config.get('export.include_duplicates', False)
    
    @include_duplicates.setter
    def include_duplicates(self, value: bool):
        """Set include duplicates setting"""
        self.config.set('export.include_duplicates', bool(value))
    
    @property
    def output_directory(self) -> str:
        """Get output directory path"""
        default_path = str(Path.home() / 'Downloads' / 'SoloScrapper')
        return self.config.get('export.output_directory', default_path)
    
    @output_directory.setter
    def output_directory(self, value: str):
        """Set output directory with validation"""
        path = Path(value)
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.config.set('export.output_directory', str(path))
        except OSError as e:
            raise ValueError(f"Invalid output directory: {e}")
    
    @property
    def filename_template(self) -> str:
        """Get filename template"""
        return self.config.get('export.filename_template', 'scraped_data_{timestamp}')
    
    @filename_template.setter
    def filename_template(self, value: str):
        """Set filename template"""
        if not value.strip():
            raise ValueError("Filename template cannot be empty")
        self.config.set('export.filename_template', value.strip())
    
    @property
    def auto_export(self) -> bool:
        """Get auto-export setting"""
        return self.config.get('export.auto_export', False)
    
    @auto_export.setter
    def auto_export(self, value: bool):
        """Set auto-export setting"""
        self.config.set('export.auto_export', bool(value))
    
    # License Settings
    @property
    def license_check_interval(self) -> int:
        """Get license check interval in seconds"""
        return self.config.get('license.check_interval', 300)
    
    @license_check_interval.setter
    def license_check_interval(self, value: int):
        """Set license check interval with validation"""
        if value < 60:
            raise ValueError("License check interval must be at least 60 seconds")
        self.config.set('license.check_interval', int(value))
    
    @property
    def auto_validate_license(self) -> bool:
        """Get auto license validation setting"""
        return self.config.get('license.auto_validate', True)
    
    @auto_validate_license.setter
    def auto_validate_license(self, value: bool):
        """Set auto license validation"""
        self.config.set('license.auto_validate', bool(value))
    
    # UI Settings
    @property
    def show_tooltips(self) -> bool:
        """Get show tooltips setting"""
        return self.config.get('ui.show_tooltips', True)
    
    @show_tooltips.setter
    def show_tooltips(self, value: bool):
        """Set show tooltips setting"""
        self.config.set('ui.show_tooltips', bool(value))
    
    @property
    def animation_enabled(self) -> bool:
        """Get animation enabled setting"""
        return self.config.get('ui.animation_enabled', True)
    
    @animation_enabled.setter
    def animation_enabled(self, value: bool):
        """Set animation enabled setting"""
        self.config.set('ui.animation_enabled', bool(value))
    
    @property
    def compact_mode(self) -> bool:
        """Get compact mode setting"""
        return self.config.get('ui.compact_mode', False)
    
    @compact_mode.setter
    def compact_mode(self, value: bool):
        """Set compact mode setting"""
        self.config.set('ui.compact_mode', bool(value))
    
    @property
    def remember_tab(self) -> bool:
        """Get remember tab setting"""
        return self.config.get('ui.remember_tab', True)
    
    @remember_tab.setter
    def remember_tab(self, value: bool):
        """Set remember tab setting"""
        self.config.set('ui.remember_tab', bool(value))
    
    @property
    def last_active_tab(self) -> int:
        """Get last active tab index"""
        return self.config.get('ui.last_active_tab', 0)
    
    @last_active_tab.setter
    def last_active_tab(self, value: int):
        """Set last active tab index"""
        self.config.set('ui.last_active_tab', max(0, int(value)))
    
    # Module Settings
    def get_enabled_modules(self) -> list:
        """Get list of enabled modules"""
        return self.config.get('modules.enabled_modules', [
            'core.scraping',
            'core.ui',
            'core.license',
            'core.database',
            'core.utils'
        ])
    
    def set_enabled_modules(self, modules: list):
        """Set enabled modules list"""
        if not isinstance(modules, list):
            raise ValueError("Modules must be a list")
        self.config.set('modules.enabled_modules', modules)
    
    def enable_module(self, module_name: str):
        """Enable a specific module"""
        modules = self.get_enabled_modules()
        if module_name not in modules:
            modules.append(module_name)
            self.set_enabled_modules(modules)
    
    def disable_module(self, module_name: str):
        """Disable a specific module"""
        modules = self.get_enabled_modules()
        if module_name in modules:
            modules.remove(module_name)
            self.set_enabled_modules(modules)
    
    def is_module_enabled(self, module_name: str) -> bool:
        """Check if a module is enabled"""
        return module_name in self.get_enabled_modules()
    
    def get_module_setting(self, module_name: str, setting_key: str, default: Any = None) -> Any:
        """Get a module-specific setting"""
        return self.config.get(f'modules.module_settings.{module_name}.{setting_key}', default)
    
    def set_module_setting(self, module_name: str, setting_key: str, value: Any):
        """Set a module-specific setting"""
        self.config.set(f'modules.module_settings.{module_name}.{setting_key}', value)
    
    # Utility Methods
    def validate_settings(self) -> Tuple[bool, list]:
        """Validate all settings
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate theme
            if self.theme not in ['dark', 'light']:
                errors.append("Invalid theme setting")
            
            # Validate scraping settings
            if self.scraping_delay < 0.5:
                errors.append("Scraping delay too low")
            
            if not (0 <= self.max_retries <= 10):
                errors.append("Invalid max retries setting")
            
            if not (10 <= self.scraping_timeout <= 300):
                errors.append("Invalid timeout setting")
            
            # Validate export format
            if self.default_export_format not in ['csv', 'json', 'xlsx']:
                errors.append("Invalid export format")
            
            # Validate output directory
            if not Path(self.output_directory).parent.exists():
                errors.append("Invalid output directory")
            
            # Validate license check interval
            if self.license_check_interval < 60:
                errors.append("License check interval too low")
                
        except Exception as e:
            errors.append(f"Settings validation error: {e}")
        
        return len(errors) == 0, errors
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        return self.config.reset_to_defaults()
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to file"""
        return self.config.export_config(file_path)
    
    def import_settings(self, file_path: str, merge: bool = True) -> bool:
        """Import settings from file"""
        return self.config.import_config(file_path, merge)