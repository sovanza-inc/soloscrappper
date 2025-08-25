#!/usr/bin/env python3
"""Main entry point for Solo Scrapper Pro.

Modular Google Maps scraper application with modern PyQt5 interface.
"""

import sys
import os
import platform
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
    
    # Set Qt attributes before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except ImportError:
    print("PyQt5 is not installed. Please install it using:")
    print("pip install PyQt5")
    sys.exit(1)

# Import core modules
try:
    from core.ui import ModernScraperGUI
    from core.config import ConfigManager, AppSettings
    from core.license import LicenseManager
    from core.utils import SystemInfo
    from core.plugins import PluginManager
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)


class SoloScrapperApp:
    """Main application class for Solo Scrapper Pro"""
    
    def __init__(self):
        """Initialize the application"""
        self.app = None
        self.main_window = None
        self.config_manager = None
        self.settings = None
        self.license_manager = None
        self.plugin_manager = None
    
    def initialize(self):
        """Initialize application components"""
        try:
            # Initialize Qt Application
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Solo Scrapper Pro")
            self.app.setApplicationVersion("2.0.0")
            self.app.setOrganizationName("Solo Scrapper")
            
            # Set cool application icon for taskbar
            icon_path = os.path.join(project_root, 'launcher_icon.svg')
            if os.path.exists(icon_path):
                self.app.setWindowIcon(QIcon(icon_path))
            else:
                # Fallback to PNG if SVG not found
                png_path = os.path.join(project_root, 'launchericon_rounded.png')
                if os.path.exists(png_path):
                    self.app.setWindowIcon(QIcon(png_path))
            
            # Initialize configuration
            self.config_manager = ConfigManager()
            self.settings = AppSettings(self.config_manager)
            
            # Initialize license manager
            self.license_manager = LicenseManager()
            
            # Initialize plugin manager
            print("Initializing plugin manager...")
            self.plugin_manager = PluginManager()
            if not self.plugin_manager.initialize():
                print("Warning: Plugin manager initialization failed")
            else:
                plugin_status = self.plugin_manager.get_plugin_status()
                print(f"Plugin manager initialized: {plugin_status['total_active']}/{plugin_status['total_available']} plugins active")
            
            # Validate settings
            is_valid, errors = self.settings.validate_settings()
            if not is_valid:
                print("Configuration validation warnings:")
                for error in errors:
                    print(f"  - {error}")
            
            return True
            
        except Exception as e:
            self.show_error("Initialization Error", 
                          f"Failed to initialize application: {str(e)}")
            return False
    
    def check_system_requirements(self):
        """Check system requirements and dependencies"""
        try:
            # Check Python version
            if sys.version_info < (3, 8):
                self.show_error("System Requirements", 
                              "Python 3.8 or higher is required.")
                return False
            
            # Check required directories
            required_dirs = ['core', 'core/ui', 'core/scraping', 'core/license', 
                           'core/database', 'core/utils', 'core/config']
            
            for dir_name in required_dirs:
                dir_path = project_root / dir_name
                if not dir_path.exists():
                    self.show_error("Missing Components", 
                                  f"Required directory '{dir_name}' not found.")
                    return False
            
            # Check for locationslist.txt
            locations_file = project_root / 'locationslist.txt'
            if not locations_file.exists():
                print("Warning: locationslist.txt not found. Location-based features may not work.")
            
            return True
            
        except Exception as e:
            self.show_error("System Check Error", 
                          f"Failed to check system requirements: {str(e)}")
            return False
    
    def create_main_window(self):
        """Create and configure the main window"""
        try:
            # Create main window
            print("Creating main window...")
            self.main_window = ModernScraperGUI()
            print("Main window created successfully")
            
            # Apply saved window geometry if available
            print("Loading window geometry...")
            geometry = self.settings.get_window_geometry()
            self.main_window.resize(geometry['width'], geometry['height'])
            self.main_window.move(geometry['x'], geometry['y'])
            print("Window geometry loaded")
            
            # Set up window close event to save geometry
            original_close_event = self.main_window.closeEvent
            
            def close_event_handler(event):
                # Save window geometry
                geometry = self.main_window.geometry()
                self.settings.set_window_geometry(
                    geometry.width(), geometry.height(),
                    geometry.x(), geometry.y()
                )
                
                # Save current tab if remember_tab is enabled
                if self.settings.remember_tab and hasattr(self.main_window, 'tab_widget'):
                    current_tab = self.main_window.tab_widget.currentIndex()
                    self.settings.last_active_tab = current_tab
                
                # Call original close event
                original_close_event(event)
            
            self.main_window.closeEvent = close_event_handler
            
            # Restore last active tab if enabled
            if (self.settings.remember_tab and 
                hasattr(self.main_window, 'tab_widget')):
                last_tab = self.settings.last_active_tab
                if 0 <= last_tab < self.main_window.tab_widget.count():
                    self.main_window.tab_widget.setCurrentIndex(last_tab)
            
            return True
            
        except Exception as e:
            self.show_error("Window Creation Error", 
                          f"Failed to create main window: {str(e)}")
            return False
    
    def show_error(self, title: str, message: str):
        """Show error message dialog"""
        if self.app:
            QMessageBox.critical(None, title, message)
        else:
            print(f"ERROR - {title}: {message}")
    
    def show_info(self, title: str, message: str):
        """Show information message dialog"""
        if self.app:
            QMessageBox.information(None, title, message)
        else:
            print(f"INFO - {title}: {message}")
    
    def run(self):
        """Run the application"""
        try:
            # Check system requirements
            if not self.check_system_requirements():
                return 1
            
            # Initialize application
            if not self.initialize():
                return 1
            
            # Create main window
            if not self.create_main_window():
                return 1
            
            print("Showing main window...")
            # Show main window
            self.main_window.show()
            
            # Print startup information
            system_info = SystemInfo()
            print(f"Solo Scrapper Pro v2.0.0")
            print(f"System: {platform.system()} {platform.release()}")
            print(f"Python: {sys.version.split()[0]}")
            print(f"Config: {self.config_manager.config_file}")
            print("Application started successfully.")
            
            print("Starting application event loop...")
            # Run the application
            result = self.app.exec_()
            print(f"Application event loop ended with result: {result}")
            return result
            
        except KeyboardInterrupt:
            print("\nApplication interrupted by user.")
            return 0
        except Exception as e:
            print(f"Error in run method: {e}")
            import traceback
            traceback.print_exc()
            self.show_error("Application Error", 
                          f"An unexpected error occurred: {str(e)}")
            return 1
        finally:
            # Cleanup
            if self.plugin_manager:
                print("Cleaning up plugin manager...")
                self.plugin_manager.cleanup()
            if self.main_window:
                self.main_window.close()
            if self.app:
                self.app.quit()


def main():
    """Main entry point"""
    # Set up error handling for unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        print(f"Uncaught exception: {exc_type.__name__}: {exc_value}")
        import traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception
    
    # Create and run application
    print("Starting Solo Scrapper application...")
    app = SoloScrapperApp()
    print("Application initialized successfully")
    exit_code = app.run()
    
    print(f"Application exited with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()