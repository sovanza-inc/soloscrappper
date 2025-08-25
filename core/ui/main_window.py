import sys
import os
import csv
import time
from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QFileDialog, 
    QMessageBox, QProgressBar, QGroupBox, QScrollArea, QFrame, QSplitter, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QCheckBox, QSlider, QStatusBar, QMenuBar, QMenu, QAction,
    QSystemTrayIcon, QStyle, QDesktopWidget, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QLinearGradient

from ..license import LicenseManager, LicenseDialog
from ..scraping import GoogleMapsScraper, ScrapingThread
from ..database import CSVHandler, DataValidator
from ..utils import LocationDataLoader, KeywordGenerator, FileUtils
from ..config import AppSettings


class ModernScraperGUI(QMainWindow):
    """Modern GUI for the Google Maps Scraper application"""
    
    def __init__(self):
        super().__init__()
        print("Initializing ModernScraperGUI...")
        self.scraped_businesses = []
        self.total_businesses = 0
        self.unique_businesses = 0
        self.scraping_thread = None
        
        print("Creating license manager...")
        self.license_manager = LicenseManager()
        print("License manager created")
        
        print("Initializing settings...")
        self.settings = AppSettings()
        print("Settings initialized")
        
        # Initialize UI
        print("Initializing UI...")
        self.init_ui()
        print("UI initialized")
        
        # Check license on startup
        print("Checking license...")
        self.check_license_on_startup()
        print("License check completed")
        
        # Setup license validation timer
        print("Setting up license validation timer...")
        self.setup_license_validation_timer()
        
        # Initial update of license status display
        print("Updating initial license status display...")
        self.update_license_status_display()
        print("ModernScraperGUI initialization completed")
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Solo Scraper")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon - using cool SVG launcher icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'launcher_icon.svg')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Fallback to PNG if SVG not found
            png_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'launchericon_rounded.png')
            if os.path.exists(png_path):
                self.setWindowIcon(QIcon(png_path))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        self.create_header(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_keywords_variation_tab()
        self.create_google_maps_tab()
        self.create_settings_tab()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply modern theme
        self.apply_modern_theme()
        
    def check_license_on_startup(self):
        """Check license validity on application startup"""
        try:
            if not self.license_manager.has_valid_cached_license():
                print("No valid cached license found")
                self.show_license_dialog()
            else:
                print("Valid cached license found")
                # Verify cached license with database periodically
                cached_key = self.license_manager.get_cached_license_key()
                if cached_key and not self.license_manager.verify_cached_license_with_database(cached_key):
                    self.show_license_dialog()
        except Exception as e:
            print(f"License check error: {e}")
            self.show_license_dialog()
                
    def setup_license_validation_timer(self):
        """Setup timer for periodic license validation"""
        self.license_timer = QTimer()
        self.license_timer.timeout.connect(self.validate_license_periodically)
        self.license_timer.start(300000)  # Check every 5 minutes
        
        # Also setup timer for updating license status display
        self.license_display_timer = QTimer()
        self.license_display_timer.timeout.connect(self.update_license_status_display)
        self.license_display_timer.start(60000)  # Update display every minute
        
    def validate_license_periodically(self):
        """Validate license periodically"""
        if not self.license_manager.has_valid_cached_license():
            QMessageBox.warning(
                self, "License Expired", 
                "Your license has expired. Please renew your license to continue using the application."
            )
            self.show_license_dialog()
        
        # Update license status display
        self.update_license_status_display()
    
    def update_license_status_display(self):
        """Update the license status card display"""
        try:
            if hasattr(self, 'license_status_card'):
                license_status = self.license_manager.get_license_status()
                status_value = self.license_status_card.findChild(QLabel, "statValue")
                if status_value:
                    status_value.setText(license_status['message'])
                    
                    # Update color based on status type
                    if license_status['type'] == 'success':
                        status_value.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    elif license_status['type'] == 'warning':
                        status_value.setStyleSheet("color: #FF9800; font-weight: bold;")
                    elif license_status['type'] == 'error':
                        status_value.setStyleSheet("color: #F44336; font-weight: bold;")
                    elif license_status['type'] == 'inactive':
                        status_value.setStyleSheet("color: #9E9E9E; font-weight: bold;")
        except Exception as e:
            print(f"Error updating license status display: {e}")
            
    def get_detailed_license_info(self) -> dict:
        """Get detailed license information"""
        try:
            cached_license = self.license_manager._load_license_cache()
            if cached_license:
                return {
                    'status': 'Valid',
                    'license_key': cached_license.get('license_key', 'Unknown'),
                    'expires_at': cached_license.get('expires_at', 'Unknown'),
                    'machine_id': self.license_manager.get_machine_id()
                }
            else:
                return {
                    'status': 'Invalid',
                    'license_key': 'None',
                    'expires_at': 'N/A',
                    'machine_id': self.license_manager.get_machine_id()
                }
        except Exception as e:
            return {
                'status': 'Error',
                'license_key': 'Error',
                'expires_at': 'Error',
                'machine_id': self.license_manager.get_machine_id(),
                'error': str(e)
            }
            
    def show_license_status_dialog(self):
        """Show detailed license status dialog"""
        license_info = self.get_detailed_license_info()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("License Status")
        dialog.setMinimumSize(450, 350)  # Allow resizing instead of fixed size
        dialog.setMaximumSize(600, 500)  # Set reasonable maximum size
        
        # Apply dark theme styling to the dialog
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 8px;
            }
            QLabel {
                color: #f0f6fc;
                font-size: 13px;
                padding: 5px;
                background-color: transparent;
            }
            QPushButton {
                background-color: #21262d;
                color: #f0f6fc;
                border: 1px solid #30363d;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Status
        status_label = QLabel(f"Status: {license_info['status']}")
        status_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #58a6ff;")
        layout.addWidget(status_label)
        
        # License Key
        key_label = QLabel(f"License Key: {license_info['license_key'][:20]}..." if len(license_info['license_key']) > 20 else f"License Key: {license_info['license_key']}")
        layout.addWidget(key_label)
        
        # Expiry
        expiry_label = QLabel(f"Expires: {license_info['expires_at']}")
        layout.addWidget(expiry_label)
        
        # Machine ID
        machine_label = QLabel(f"Machine ID: {license_info['machine_id']}")
        layout.addWidget(machine_label)
        
        # Error if any
        if 'error' in license_info:
            error_label = QLabel(f"Error: {license_info['error']}")
            error_label.setStyleSheet("color: #f44336; font-weight: bold;")
            layout.addWidget(error_label)
        
        # Add stretch to push buttons to bottom
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        unbind_btn = QPushButton("Remove License Binding")
        unbind_btn.clicked.connect(lambda: self.unbind_license())
        button_layout.addWidget(unbind_btn)
        
        reauth_btn = QPushButton("Re-authenticate")
        reauth_btn.clicked.connect(lambda: self.show_license_dialog())
        button_layout.addWidget(reauth_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
        
    def unbind_license(self):
        """Unbind the current license"""
        reply = QMessageBox.question(
            self, "Unbind License", 
            "Are you sure you want to unbind this license? You will need to re-authenticate.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.license_manager.clear_license_cache()
            QMessageBox.information(self, "License Unbound", "License has been unbound successfully.")
            self.show_license_dialog()
            
    def show_license_dialog(self):
        """Show license dialog for re-authentication"""
        dialog = LicenseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # License validated successfully
            pass
        else:
            # User cancelled or license validation failed
            sys.exit()
            
    def create_header(self, main_layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setObjectName("headerFrame")
        main_layout.addWidget(header_frame)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo and title
        title_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        if os.path.exists('launchericon_rounded.png'):
            pixmap = QPixmap('launchericon_rounded.png')
            scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("🗺️")
            logo_label.setStyleSheet("font-size: 30px;")
        
        title_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("Solo Scrapper")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        # Header buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.clicked.connect(self.show_settings_tab)
        buttons_layout.addWidget(settings_btn)
        
        # License button
        license_btn = QPushButton("License")
        license_btn.setObjectName("licenseBtn")
        license_btn.clicked.connect(self.show_license_status_dialog)
        buttons_layout.addWidget(license_btn)
        
        header_layout.addLayout(buttons_layout)
        
    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        dashboard_widget = QWidget()
        dashboard_widget.setObjectName("dashboardTab")
        dashboard_widget.setStyleSheet("QWidget#dashboardTab { background-color: #0d1117; }")
        self.tab_widget.addTab(dashboard_widget, "📊 Dashboard")
        
        # Main scroll area for better content management
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { background-color: #0d1117; border: none; }")
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("QWidget { background-color: #0d1117; }")
        scroll_area.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(dashboard_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Dashboard title
        title_label = QLabel("Scraping Dashboard")
        title_label.setObjectName("dashboardTitle")
        layout.addWidget(title_label)
        
        # Stats section
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        layout.addWidget(stats_frame)
        
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        
        # Set column stretch to distribute space evenly
        stats_layout.setColumnStretch(0, 1)
        stats_layout.setColumnStretch(1, 1)
        stats_layout.setColumnStretch(2, 1)
        
        # Create stat cards
        self.total_businesses_card = self.create_stat_card("Total Businesses", "0", "📊")
        self.unique_businesses_card = self.create_stat_card("Unique Businesses", "0", "🎯")
        self.success_rate_card = self.create_stat_card("Success Rate", "0%", "✅")
        self.current_keyword_card = self.create_stat_card("Current Keyword", "Ready", "🔍")
        self.keywords_processed_card = self.create_stat_card("Keywords Processed", "0", "📝")
        self.scraping_status_card = self.create_stat_card("Status", "⏸️ Idle", "⚡")
        
        # Add license status card
        license_status = self.license_manager.get_license_status()
        self.license_status_card = self.create_stat_card(
            "License Status", 
            license_status['message'], 
            "🔑",
            click_handler=self.show_license_status_dialog
        )
        
        # Use proper grid layout with better spacing and distribution
        stats_layout.addWidget(self.total_businesses_card, 0, 0)
        stats_layout.addWidget(self.unique_businesses_card, 0, 1)
        stats_layout.addWidget(self.success_rate_card, 0, 2)
        stats_layout.addWidget(self.current_keyword_card, 1, 0)
        stats_layout.addWidget(self.keywords_processed_card, 1, 1)
        stats_layout.addWidget(self.scraping_status_card, 1, 2)
        stats_layout.addWidget(self.license_status_card, 2, 0, 1, 3)  # Span across 3 columns
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        layout.addWidget(progress_frame)
        
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(20, 20, 20, 20)
        progress_layout.setSpacing(15)
        
        progress_title = QLabel("Scraping Progress")
        progress_title.setObjectName("progressTitle")
        progress_layout.addWidget(progress_title)
        
        self.dashboard_progress_bar = QProgressBar()
        self.dashboard_progress_bar.setObjectName("dashboardProgressBar")
        self.dashboard_progress_bar.setFormat("Ready to start scraping...")
        progress_layout.addWidget(self.dashboard_progress_bar)
        
        # Activity log
        activity_title = QLabel("Recent Activity")
        activity_title.setObjectName("activityTitle")
        progress_layout.addWidget(activity_title)
        
        self.dashboard_activity_log = QTextEdit()
        self.dashboard_activity_log.setObjectName("dashboardActivityLog")
        self.dashboard_activity_log.setMinimumHeight(200)
        self.dashboard_activity_log.setMaximumHeight(300)
        self.dashboard_activity_log.setReadOnly(True)
        self.dashboard_activity_log.append("[Dashboard] Ready to start scraping...")
        progress_layout.addWidget(self.dashboard_activity_log)
        
        # Add stretch to push content to top and ensure proper spacing
        layout.addStretch()
        
    def create_stat_card(self, title: str, value: str, icon: str, click_handler=None) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(120)
        card.setMaximumHeight(140)
        card.setMinimumWidth(200)
        
        # Make card clickable if click_handler is provided
        if click_handler:
            card.setCursor(Qt.PointingHandCursor)
            card.mousePressEvent = lambda event: click_handler() if event.button() == Qt.LeftButton else None
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("statIcon")
        icon_label.setMinimumSize(24, 24)
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        return card
        
    def create_keywords_variation_tab(self):
        """Create the keywords variation tab with modern UI"""
        keywords_widget = QWidget()
        keywords_widget.setObjectName("keywordsTab")
        keywords_widget.setStyleSheet("QWidget#keywordsTab { background-color: #0d1117; }")
        self.tab_widget.addTab(keywords_widget, "🔤 Keyword Variations")
        
        # Main scroll area for better content management
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { background-color: #0d1117; border: none; }")
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("QWidget { background-color: #0d1117; }")
        scroll_area.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(keywords_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_area)
        
        # Set the main layout background
        keywords_widget.setStyleSheet("""
            QWidget#keywordsTab { 
                background-color: #0d1117; 
            }
            QVBoxLayout { 
                background-color: #0d1117; 
            }
        """)
        
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Modern title with dark background
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel("🔤 Keyword Variations Generator")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #f0f6fc;
            background: transparent;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addWidget(title_frame)
        
        # Input Keywords Card
        input_card = QFrame()
        input_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)
        
        # Card header
        input_header = QLabel("📝 Base Keywords")
        input_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        """)
        input_layout.addWidget(input_header)
        
        # Keywords input with modern styling
        keywords_label = QLabel("Enter your base keywords (one per line):")
        keywords_label.setStyleSheet("""
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 5px;
        """)
        input_layout.addWidget(keywords_label)
        
        self.base_keyword_input = QTextEdit()
        self.base_keyword_input.setMaximumHeight(120)
        self.base_keyword_input.setPlaceholderText("Enter keywords, one per line...\n\nExamples:\n• restaurant\n• cafe\n• hotel\n• gym")
        self.base_keyword_input.setStyleSheet("""
            QTextEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 2px solid #1f6feb;
                background-color: #0d1117;
            }
        """)
        input_layout.addWidget(self.base_keyword_input)
        
        layout.addWidget(input_card)
        
        # Location Selection Card
        location_card = QFrame()
        location_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        location_layout = QVBoxLayout(location_card)
        location_layout.setContentsMargins(20, 20, 20, 20)
        location_layout.setSpacing(15)
        
        # Location header
        location_header = QLabel("🌍 Location Targeting")
        location_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        """)
        location_layout.addWidget(location_header)
        
        # Location selection grid
        location_grid = QGridLayout()
        location_grid.setSpacing(15)
        
        # Country selection
        country_label = QLabel("Country:")
        country_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #8b949e;
        """)
        location_grid.addWidget(country_label, 0, 0)
        
        self.country_combo = QComboBox()
        self.country_combo.setStyleSheet("""
            QComboBox {
                background-color: #161b22;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 150px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #1f6feb;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f0f6fc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #f0f6fc;
                selection-background-color: #1f6feb;
                border: 1px solid #30363d;
                border-radius: 4px;
            }
        """)
        self.country_combo.currentTextChanged.connect(self.on_country_changed)
        location_grid.addWidget(self.country_combo, 0, 1)
        
        
        # State selection
        state_label = QLabel("State/Province:")
        state_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #8b949e;
        """)
        location_grid.addWidget(state_label, 0, 2)
        
        self.state_combo = QComboBox()
        self.state_combo.setStyleSheet("""
            QComboBox {
                background-color: #161b22;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 150px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #1f6feb;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f0f6fc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #f0f6fc;
                selection-background-color: #1f6feb;
                border: 1px solid #30363d;
                border-radius: 4px;
            }
        """)
        self.state_combo.currentTextChanged.connect(self.on_state_changed)
        location_grid.addWidget(self.state_combo, 0, 3)
        
        # City selection
        city_label = QLabel("City:")
        city_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #8b949e;
        """)
        location_grid.addWidget(city_label, 1, 0)
        
        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet("""
            QComboBox {
                background-color: #161b22;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 150px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #1f6feb;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f0f6fc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #f0f6fc;
                selection-background-color: #1f6feb;
                border: 1px solid #30363d;
                border-radius: 4px;
            }
        """)
        location_grid.addWidget(self.city_combo, 1, 1, 1, 3)
        
        location_layout.addLayout(location_grid)
        layout.addWidget(location_card)
        
        # Action Buttons Card
        actions_card = QFrame()
        actions_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(15)
        
        # Actions header
        actions_header = QLabel("⚡ Actions")
        actions_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        """)
        actions_layout.addWidget(actions_header)
        
        # Button grid for better organization
        button_grid = QGridLayout()
        button_grid.setSpacing(12)
        
        # Generate button (primary action)
        generate_btn = QPushButton("🚀 Generate Variations")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        generate_btn.clicked.connect(self.generate_keyword_variations)
        button_grid.addWidget(generate_btn, 0, 0)
        
        # Copy to scraper button
        copy_btn = QPushButton("📋 Copy to Scraper")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        copy_btn.clicked.connect(self.copy_to_scraper)
        button_grid.addWidget(copy_btn, 0, 1)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #f39c12;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        clear_btn.clicked.connect(self.clear_keyword_variations)
        button_grid.addWidget(clear_btn, 0, 2)
        
        actions_layout.addLayout(button_grid)
        layout.addWidget(actions_card)
        
        # Output Results Card
        output_card = QFrame()
        output_card.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(15)
        
        # Output header
        output_header = QLabel("📊 Generated Variations")
        output_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        """)
        output_layout.addWidget(output_header)
        
        # Output text area with modern styling
        self.variations_output = QTextEdit()
        self.variations_output.setReadOnly(True)
        self.variations_output.setPlaceholderText("Generated keyword variations will appear here...\n\nClick 'Generate Variations' to start!")
        self.variations_output.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 15px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.5;
                min-height: 200px;
            }
            QTextEdit:focus {
                border: 2px solid #1f6feb;
            }
        """)
        output_layout.addWidget(self.variations_output)
        
        layout.addWidget(output_card)
        
        # Load location data
        self.load_location_data()
        
    def generate_keyword_variations(self):
        """Generate keyword variations based on input"""
        base_keywords = self.base_keyword_input.toPlainText().strip().split('\n')
        base_keywords = [kw.strip() for kw in base_keywords if kw.strip()]
        
        if not base_keywords:
            QMessageBox.warning(self, "No Keywords", "Please enter at least one base keyword.")
            return
        
        selected_locations = self.get_selected_locations()
        
        if not selected_locations:
            QMessageBox.warning(self, "No Locations", "Please select at least one location.")
            return
        
        variations = []
        
        for keyword in base_keywords:
            for location in selected_locations:
                variations.append(f"{keyword} in {location}")
        
        # Remove duplicates while preserving order
        unique_variations = list(dict.fromkeys(variations))
        
        self.variations_output.setPlainText('\n'.join(unique_variations))
        
        QMessageBox.information(
            self, "Variations Generated", 
            f"Generated {len(unique_variations)} unique keyword variations!"
        )
        
    def clear_keyword_variations(self):
        """Clear keyword variations"""
        self.base_keyword_input.clear()
        self.variations_output.clear()
        
    def copy_to_scraper(self):
        """Copy generated variations to the scraper tab"""
        variations = self.variations_output.toPlainText().strip()
        
        if not variations:
            QMessageBox.warning(self, "No Variations", "No variations to copy. Please generate variations first.")
            return
        
        # Switch to Google Maps tab and populate keywords
        self.tab_widget.setCurrentIndex(2)  # Google Maps tab is index 2
        self.keywords_input.setPlainText(variations)
        
        QMessageBox.information(self, "Copied", "Keyword variations copied to scraper!")
        
    def load_location_data(self):
        """Load location data from global_locations.json"""
        # Initialize location data loader
        self.location_loader = LocationDataLoader()
        self.location_data = self.location_loader.get_location_data()
        
        if not self.location_data:
            print("Warning: No location data loaded, using fallback data")
            # Fallback data if global_locations.json is not available
            self.location_data = {
                "United States": {
                    "California": ["Los Angeles", "San Francisco", "San Diego"],
                    "New York": ["New York City", "Buffalo", "Rochester"],
                    "Texas": ["Houston", "Dallas", "Austin"]
                },
                "Canada": {
                    "Ontario": ["Toronto", "Ottawa", "Hamilton"],
                    "Quebec": ["Montreal", "Quebec City", "Laval"]
                }
            }
        
        # Populate country dropdown
        countries = ["All Countries"] + sorted(self.location_data.keys())
        self.country_combo.addItems(countries)
        
        # Populate state dropdown with all states initially
        all_states = ["All States"]
        for country_data in self.location_data.values():
            all_states.extend(sorted(country_data.keys()))
        self.state_combo.addItems(all_states)
        
    def on_country_changed(self, country):
        """Handle country selection change"""
        self.state_combo.clear()
        self.city_combo.clear()
        
        if country == "All Countries":
            # Show all states from all countries
            all_states = ["All States"]
            for country_data in self.location_data.values():
                all_states.extend(sorted(country_data.keys()))
            self.state_combo.addItems(all_states)
        elif country in self.location_data:
            # Show states for selected country
            states = ["All States"] + sorted(self.location_data[country].keys())
            self.state_combo.addItems(states)
        
        # Add default city option
        self.city_combo.addItem("All Cities")
    
    def on_state_changed(self, state):
        """Handle state selection change"""
        self.city_combo.clear()
        
        if state == "All States":
            self.city_combo.addItem("All Cities")
        else:
            # Find the state in any country
            cities_found = False
            for country_data in self.location_data.values():
                if state in country_data:
                    cities = [f"All Cities in {state}"] + country_data[state]
                    self.city_combo.addItems(cities)
                    cities_found = True
                    break
            
            if not cities_found:
                self.city_combo.addItem("All Cities")
            
    def get_selected_locations(self) -> List[str]:
        """Get selected locations for keyword generation"""
        locations = []
        
        country = self.country_combo.currentText()
        state = self.state_combo.currentText()
        city = self.city_combo.currentText()
        
        if country == "All Countries":
            if state == "All States":
                if city == "All Cities":
                    # Add all countries, states and cities
                    for country_name, country_data in self.location_data.items():
                        locations.append(country_name)
                        for state_name, cities in country_data.items():
                            locations.append(state_name)
                            locations.extend(cities)
                else:
                    # Add all countries and states
                    for country_name, country_data in self.location_data.items():
                        locations.append(country_name)
                        locations.extend(list(country_data.keys()))
            else:
                # Find the specific state across all countries
                for country_data in self.location_data.values():
                    if state in country_data:
                        if city == f"All Cities in {state}":
                            locations.append(state)
                            locations.extend(country_data[state])
                        elif city in country_data[state]:
                            locations.append(f"{city}, {state}")
                            locations.append(city)
                            locations.append(state)
                        else:
                            locations.append(state)
                        break
        elif country in self.location_data:
            country_data = self.location_data[country]
            if state == "All States":
                if city == "All Cities":
                    # Add country and all its states and cities
                    locations.append(country)
                    for state_name, cities in country_data.items():
                        locations.append(state_name)
                        locations.extend(cities)
                else:
                    # Add country and all its states
                    locations.append(country)
                    locations.extend(list(country_data.keys()))
            elif state in country_data:
                if city == f"All Cities in {state}":
                    # Add country, state and all its cities
                    locations.append(country)
                    locations.append(state)
                    locations.extend(country_data[state])
                elif city in country_data[state]:
                    # Add specific city, state and country
                    locations.append(f"{city}, {state}, {country}")
                    locations.append(f"{city}, {state}")
                    locations.append(city)
                    locations.append(state)
                    locations.append(country)
                else:
                    # Add just the state and country
                    locations.append(f"{state}, {country}")
                    locations.append(state)
                    locations.append(country)
        
        return locations
        
    def create_google_maps_tab(self):
        """Create the Google Maps scraper tab"""
        maps_widget = QWidget()
        maps_widget.setObjectName("mapsTab")
        maps_widget.setStyleSheet("QWidget#mapsTab { background-color: #0d1117; }")
        self.tab_widget.addTab(maps_widget, "🗺️ Google Maps Scraper")
        
        # Main scroll area for better content management
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { background-color: #0d1117; border: none; }")
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("QWidget { background-color: #0d1117; }")
        scroll_area.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(maps_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_area)
        
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Control section
        control_frame = QFrame()
        control_frame.setObjectName("controlFrame")
        layout.addWidget(control_frame)
        
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 20, 20, 20)
        control_layout.setSpacing(15)
        
        # Keywords input
        keywords_label = QLabel("Keywords to scrape (one per line):")
        keywords_label.setObjectName("inputLabel")
        control_layout.addWidget(keywords_label)
        
        self.keywords_input = QTextEdit()
        self.keywords_input.setObjectName("keywordsInput")
        self.keywords_input.setMaximumHeight(120)
        self.keywords_input.setPlaceholderText("Enter keywords to search for...\ne.g.:\nrestaurant in New York\ncafe near Los Angeles\nbar in Chicago")
        control_layout.addWidget(self.keywords_input)
        
        # Settings row
        settings_layout = QHBoxLayout()
        
        # Max results
        max_results_label = QLabel("Max results per keyword:")
        max_results_label.setObjectName("inputLabel")
        settings_layout.addWidget(max_results_label)
        
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setObjectName("maxResultsSpin")
        self.max_results_spin.setMinimum(1)
        self.max_results_spin.setMaximum(1000)
        self.max_results_spin.setValue(50)
        settings_layout.addWidget(self.max_results_spin)
        
        settings_layout.addStretch()
        control_layout.addLayout(settings_layout)
        
        # Control buttons
        self.create_control_buttons(control_layout)
        
        # Progress section
        progress_label = QLabel("Progress:")
        progress_label.setObjectName("inputLabel")
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        layout.addWidget(self.progress_bar)
        
        self.progress_log = QTextEdit()
        self.progress_log.setObjectName("progressLog")
        self.progress_log.setMaximumHeight(100)
        self.progress_log.setReadOnly(True)
        layout.addWidget(self.progress_log)
        
        # Results section
        self.create_results_table(layout)
        
        # Add stretch to push content to top and ensure proper spacing
        layout.addStretch()
        
    def create_control_buttons(self, layout):
        """Create control buttons for scraping"""
        # Use grid layout for better organization and to prevent horizontal overflow
        button_layout = QGridLayout()
        button_layout.setSpacing(10)
        
        # Row 1: Main control buttons
        self.start_btn = QPushButton("Start Scraping")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_scraping)
        button_layout.addWidget(self.start_btn, 0, 0)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.clicked.connect(self.pause_scraping)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn, 0, 1)
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setObjectName("resumeBtn")
        self.resume_btn.clicked.connect(self.resume_scraping)
        self.resume_btn.setEnabled(False)
        button_layout.addWidget(self.resume_btn, 0, 2)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_scraping)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn, 0, 3)
        
        # Row 2: Export and utility buttons
        self.save_btn = QPushButton("Export All to CSV")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self.save_all_csv)
        button_layout.addWidget(self.save_btn, 1, 0)
        
        self.save_unique_btn = QPushButton("Export Unique to CSV")
        self.save_unique_btn.setObjectName("saveUniqueBtn")
        self.save_unique_btn.clicked.connect(self.save_unique_csv)
        button_layout.addWidget(self.save_unique_btn, 1, 1)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_btn, 1, 2)
        
        layout.addLayout(button_layout)
        
    def create_results_table(self, layout):
        """Create results table"""
        results_label = QLabel("Results:")
        results_label.setObjectName("inputLabel")
        layout.addWidget(results_label)
        
        results_frame = QFrame()
        results_frame.setObjectName("resultsFrame")
        layout.addWidget(results_frame)
        
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(15)
        
        self.results_table = QTableWidget()
        self.results_table.setObjectName("resultsTable")
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Keyword", "Name", "Website", "Phone", "Address", "Rating", "Category"
        ])
        
        # Set size policies to prevent horizontal scrolling
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(False)  # Don't stretch last section
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow manual resizing
        
        # Set optimized column widths that fit within the window (total: ~950px)
        header.resizeSection(0, 120)  # Keyword - compact
        header.resizeSection(1, 180)  # Name - reasonable
        header.resizeSection(2, 150)  # Website - compact
        header.resizeSection(3, 100)  # Phone - compact
        header.resizeSection(4, 200)  # Address - larger for addresses
        header.resizeSection(5, 80)   # Rating - compact
        header.resizeSection(6, 120)  # Category - reasonable
        
        results_layout.addWidget(self.results_table)
        
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_widget = QWidget()
        self.tab_widget.addTab(settings_widget, "⚙️ Settings")
        
        layout = QVBoxLayout(settings_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Settings title
        title_label = QLabel("Application Settings")
        title_label.setObjectName("settingsTitle")
        layout.addWidget(title_label)
        
        # Default Save Directory Section
        save_dir_group = QGroupBox("Default Save Directory")
        save_dir_group.setObjectName("settingsGroup")
        save_dir_layout = QVBoxLayout(save_dir_group)
        
        # Current directory display
        current_dir_layout = QHBoxLayout()
        current_dir_label = QLabel("Current Directory:")
        self.current_dir_display = QLabel(self.settings.output_directory)
        self.current_dir_display.setObjectName("currentDirDisplay")
        self.current_dir_display.setWordWrap(True)
        current_dir_layout.addWidget(current_dir_label)
        current_dir_layout.addWidget(self.current_dir_display, 1)
        save_dir_layout.addLayout(current_dir_layout)
        
        # Change directory button
        change_dir_btn = QPushButton("Change Directory")
        change_dir_btn.setObjectName("changeDirBtn")
        change_dir_btn.clicked.connect(self.change_save_directory)
        save_dir_layout.addWidget(change_dir_btn)
        
        # Reset to default button
        reset_dir_btn = QPushButton("Reset to Default")
        reset_dir_btn.setObjectName("resetDirBtn")
        reset_dir_btn.clicked.connect(self.reset_save_directory)
        save_dir_layout.addWidget(reset_dir_btn)
        
        layout.addWidget(save_dir_group)
        
        # Add stretch to push content to top
        layout.addStretch()
        
    def show_settings_tab(self):
        """Show the settings tab"""
        # Find the settings tab index and switch to it
        for i in range(self.tab_widget.count()):
            if "Settings" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                break
                
    def change_save_directory(self):
        """Open dialog to change the default save directory"""
        current_dir = self.settings.output_directory
        new_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Default Save Directory", 
            current_dir
        )
        
        if new_dir:
            try:
                self.settings.output_directory = new_dir
                self.current_dir_display.setText(new_dir)
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Default save directory updated to:\n{new_dir}"
                )
            except ValueError as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Failed to set directory: {str(e)}"
                )
                
    def reset_save_directory(self):
        """Reset save directory to default"""
        default_path = str(Path.home() / 'Downloads' / 'SoloScrapper')
        try:
            self.settings.output_directory = default_path
            self.current_dir_display.setText(default_path)
            QMessageBox.information(
                self, 
                "Success", 
                f"Default save directory reset to:\n{default_path}"
            )
        except ValueError as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Failed to reset directory: {str(e)}"
            )
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def apply_modern_theme(self):
        """Apply modern dark theme to the application"""
        self.setStyleSheet("""
            /* Scroll Area Styling */
            QScrollArea {
                background-color: #0d1117;
                border: none;
                outline: none;
            }
            
            QScrollBar:vertical {
                background-color: #21262d;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #484f58;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #58a6ff;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: transparent;
            }
            
            /* Main Window */
            QMainWindow {
                background-color: #0d1117;
                color: #f0f6fc;
            }
            
            /* Header */
            #headerFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #161b22, stop: 1 #21262d);
                border-bottom: 2px solid #58a6ff;
            }
            
            #titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                margin-left: 10px;
            }
            
            #licenseBtn {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
                font-family: Arial;
            }

            #licenseBtn:hover {
                background-color: #005a9e;
                color: #ffffff;
            }
            
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #0d1117;
            }
            
            QTabBar::tab {
                background-color: #21262d;
                color: #f0f6fc;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #58a6ff;
            }
            
            QTabBar::tab:hover {
                background-color: #30363d;
            }
            
            /* Input Fields */
            QTextEdit, QLineEdit {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            
            QTextEdit:focus, QLineEdit:focus {
                border: 2px solid #58a6ff;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #21262d;
                color: #f0f6fc;
                border: 1px solid #30363d;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                font-family: Arial;
                text-align: center;
                min-width: 100px;
            }

            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
                color: #f0f6fc;
            }

            QPushButton:pressed {
                background-color: #161b22;
                color: #f0f6fc;
            }

            QPushButton:disabled {
                background-color: #21262d;
                color: #6e7681;
            }
            
            /* Specific Button Styles */
            #startBtn {
                background-color: #16a085;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #startBtn:hover {
                background-color: #1abc9c;
                color: #ffffff;
            }

            #pauseBtn, #resumeBtn {
                background-color: #f39c12;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #pauseBtn:hover, #resumeBtn:hover {
                background-color: #e67e22;
                color: #ffffff;
            }

            #stopBtn {
                background-color: #e74c3c;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #stopBtn:hover {
                background-color: #c0392b;
                color: #ffffff;
            }

            #saveBtn, #saveUniqueBtn {
                background-color: #8e44ad;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #saveBtn:hover, #saveUniqueBtn:hover {
                background-color: #9b59b6;
                color: #ffffff;
            }

            #clearBtn {
                background-color: #95a5a6;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #clearBtn:hover {
                background-color: #7f8c8d;
                color: #ffffff;
            }
            
            #copyBtn {
                background-color: #3498db;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #copyBtn:hover {
                background-color: #2980b9;
                color: #ffffff;
            }

            #generateBtn {
                background-color: #27ae60;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #generateBtn:hover {
                background-color: #2ecc71;
                color: #ffffff;
            }

            #clearVariationsBtn {
                background-color: #e67e22;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #clearVariationsBtn:hover {
                background-color: #d35400;
                color: #ffffff;
            }

            #copyToScraperBtn {
                background-color: #9b59b6;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }

            #copyToScraperBtn:hover {
                background-color: #8e44ad;
                color: #ffffff;
            }
            
            /* Results Table */
            #resultsFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            
            #resultsTable {
                background-color: #0d1117;
                alternate-background-color: #161b22;
                color: #f0f6fc;
                gridline-color: #30363d;
                border: none;
            }
            
            QHeaderView::section {
                background-color: #21262d;
                color: #f0f6fc;
                padding: 8px;
                border: 1px solid #30363d;
                font-weight: bold;
            }
            
            /* Progress Log */
            #progressLog {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            
            /* Labels */
            #sectionTitle {
                font-size: 18px;
                font-weight: bold;
                color: #f0f6fc;
                margin-bottom: 10px;
            }
            
            #inputLabel {
                font-size: 12px;
                font-weight: bold;
                color: #8b949e;
                margin-bottom: 5px;
            }
            
            /* Input Fields */
            #baseKeywordInput, #keywordsInput {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            
            #keywordsInput:focus {
                border: 2px solid #1f6feb;
                background-color: #161b22;
            }
            
            /* Combo Boxes */
            #countryCombo, #stateCombo, #cityCombo {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
                min-width: 120px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f0f6fc;
                margin-right: 5px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #21262d;
                color: #f0f6fc;
                selection-background-color: #58a6ff;
                border: 1px solid #30363d;
            }
            
            /* Status Bar */
            #statusBar {
                background-color: #0d1117;
                color: #f0f6fc;
                border-top: 1px solid #30363d;
            }
            
            /* Dashboard Styles */
            QWidget#dashboardTab {
                background-color: #0d1117;
            }
            
            #dashboardTitle {
                font-size: 24px;
                font-weight: bold;
                color: #f0f6fc;
                margin-bottom: 20px;
                background-color: #0d1117;
            }
            
            #statsFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 10px;
            }
            
            #statCard {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin: 5px;
                padding: 5px;
                min-width: 200px;
                min-height: 120px;
            }
            
            #statCard:hover {
                border: 2px solid #58a6ff;
                background-color: #1c2128;
            }
            
            #statIcon {
                font-size: 24px;
                margin-right: 8px;
                min-width: 24px;
                min-height: 24px;
            }
            
            #statTitle {
                font-size: 12px;
                color: #8b949e;
                font-weight: 600;
                line-height: 1.2;
                word-wrap: break-word;
            }
            
            #statValue {
                font-size: 20px;
                font-weight: bold;
                color: #f0f6fc;
                margin-top: 5px;
                text-align: center;
            }
            
            #progressFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 10px;
            }
            
            #progressTitle, #activityTitle {
                font-size: 16px;
                font-weight: bold;
                color: #f0f6fc;
                margin-bottom: 12px;
                background-color: #0d1117;
            }
            
            #dashboardProgressBar {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                text-align: center;
                color: #f0f6fc;
                font-weight: bold;
                height: 25px;
                margin-bottom: 10px;
            }
            
            #dashboardProgressBar::chunk {
                background-color: #58a6ff;
                border-radius: 4px;
            }
            
            #dashboardActivityLog {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 12px;
                line-height: 1.4;
            }
            
            /* Progress Bar */
            QProgressBar, #progressBar {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                text-align: center;
                color: #f0f6fc;
                font-weight: bold;
                height: 20px;
            }
            
            QProgressBar::chunk, #progressBar::chunk {
                background-color: #58a6ff;
                border-radius: 4px;
            }
            
            /* Spin Box */
            QSpinBox, #maxResultsSpin {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
                min-width: 80px;
            }
            
            #maxResultsSpin:focus {
                border: 2px solid #1f6feb;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #21262d;
                border: none;
                width: 16px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #58a6ff;
            }
            
            /* Frames */
            #inputFrame, #controlFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            
            /* Settings Tab Styles */
            #settingsTitle {
                color: #f0f6fc;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
            
            #settingsGroup {
                background-color: #0d1117;
                border: 2px solid #30363d;
                border-radius: 12px;
                padding: 15px;
                margin: 10px;
            }
            
            #settingsGroup QLabel {
                color: #f0f6fc;
                font-size: 14px;
                font-weight: bold;
            }
            
            /* Group Box Title Styling */
            QGroupBox {
                color: #f0f6fc;
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
            }
            
            QGroupBox::title {
                color: #f0f6fc;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            #currentDirDisplay {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                color: #8b949e;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            
            #changeDirBtn, #resetDirBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a9eff, stop:1 #0078d4);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
            }
            
            #changeDirBtn:hover, #resetDirBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5ba7ff, stop:1 #106ebe);
            }
            
            #changeDirBtn:pressed, #resetDirBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a8eef, stop:1 #0066c4);
            }
            
            /* Keywords Tab Styles */
            QWidget#keywordsTab {
                background-color: #0d1117;
            }
            
            QWidget#keywordsTab QFrame {
                background-color: #0d1117;
            }
            
            QWidget#keywordsTab QLabel {
                background-color: transparent;
            }
            
            QWidget#keywordsTab QTextEdit {
                background-color: #161b22;
            }
            
            QWidget#keywordsTab QComboBox {
                background-color: #161b22;
            }
            
            /* Maps Tab Styles */
            QWidget#mapsTab {
                background-color: #0d1117;
            }
            
            QWidget#mapsTab QFrame {
                background-color: #0d1117;
            }
            
            QWidget#mapsTab QLabel {
                background-color: transparent;
            }
            
            QWidget#mapsTab QTextEdit {
                background-color: #161b22;
            }
            
            QWidget#mapsTab QSpinBox {
                background-color: #161b22;
            }
            
            QWidget#mapsTab QTableWidget {
                background-color: #0d1117;
            }
            
            /* Dashboard Styles */
            QWidget#dashboardTab {
                background-color: #0d1117;
            }
            
            /* Dialog Styling */
            QDialog {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 2px solid #30363d;
                border-radius: 8px;
            }
            
            QDialog QLabel {
                color: #f0f6fc;
                background-color: transparent;
            }
            
            QDialog QPushButton {
                background-color: #21262d;
                color: #f0f6fc;
                border: 1px solid #30363d;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            
            QDialog QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
            }
            
            QDialog QPushButton:pressed {
                background-color: #161b22;
            }
            
            /* Group Box Title Styling */
            QGroupBox {
                color: #f0f6fc;
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
            }
        """)
        
    def show_license_dialog(self):
        """Show license dialog"""
        dialog = LicenseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # License validated successfully
            pass
        else:
            # User cancelled or license validation failed
            sys.exit()
            
    def start_scraping(self):
        """Start the scraping process"""
        keywords_text = self.keywords_input.toPlainText().strip()
        if not keywords_text:
            QMessageBox.warning(self, "No Keywords", "Please enter keywords to scrape.")
            return
        
        keywords = [kw.strip() for kw in keywords_text.split('\n') if kw.strip()]
        max_results = self.max_results_spin.value()
        
        # Update dashboard status
        if hasattr(self, 'scraping_status_card'):
            status_value = self.scraping_status_card.findChild(QLabel, "statValue")
            if status_value:
                status_value.setText("🔄 Starting...")
        
        # Get Chrome settings - using defaults for macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        profile_path = str(Path.home() / "Library/Application Support/Google/Chrome")
        output_file = str(Path.home() / "Desktop" / "google_maps_results.csv")
        
        # Create and start scraping thread
        self.scraping_thread = ScrapingThread(keywords, chrome_path, profile_path, output_file)
        self.scraping_thread.progress_signal.connect(self.log_progress)
        self.scraping_thread.business_signal.connect(self.add_business_to_table)
        self.scraping_thread.business_signal.connect(self.update_dashboard_stats)
        self.scraping_thread.keyword_signal.connect(self.update_current_keyword)
        self.scraping_thread.keyword_signal.connect(self.update_dashboard_keyword)
        self.scraping_thread.finished_signal.connect(self.scraping_finished)
        
        self.scraping_thread.start()
        
        # Update button states
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        self.log_progress("🚀 Scraping started...")
        
    def pause_scraping(self):
        """Pause the scraping process"""
        if self.scraping_thread:
            self.scraping_thread.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.log_progress("⏸️ Scraping paused")
            
            # Update dashboard status
            if hasattr(self, 'scraping_status_card'):
                status_value = self.scraping_status_card.findChild(QLabel, "statValue")
                if status_value:
                    status_value.setText("⏸️ Paused")
                    
    def resume_scraping(self):
        """Resume the scraping process"""
        if self.scraping_thread:
            self.scraping_thread.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.log_progress("▶️ Scraping resumed")
            
            # Update dashboard status
            if hasattr(self, 'scraping_status_card'):
                status_value = self.scraping_status_card.findChild(QLabel, "statValue")
                if status_value:
                    status_value.setText("🔄 Scraping")
                    
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraping_thread:
            self.scraping_thread.stop()
            self.scraping_thread.wait()  # Wait for thread to finish
            
        # Reset button states
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        self.log_progress("⏹️ Scraping stopped")
        
        # Update dashboard status
        if hasattr(self, 'scraping_status_card'):
            status_value = self.scraping_status_card.findChild(QLabel, "statValue")
            if status_value:
                status_value.setText("⏹️ Stopped")
                
    def save_all_csv(self):
        """Save all results to CSV"""
        if not self.scraped_businesses:
            QMessageBox.warning(self, "No Data", "No businesses to save")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save All Results", 
            str(Path.home() / "Desktop" / "all_businesses.csv"),
            "CSV Files (*.csv)"
        )
        
        if file_path:
            self._save_to_csv(self.scraped_businesses, file_path)
            QMessageBox.information(self, "Success", f"Saved {len(self.scraped_businesses)} businesses to {file_path}")
            
    def save_unique_csv(self):
        """Save unique results to CSV"""
        if not self.scraped_businesses:
            QMessageBox.warning(self, "No Data", "No businesses to save")
            return
        
        # Remove duplicates based on business name and address
        unique_businesses = []
        seen = set()
        
        for business in self.scraped_businesses:
            key = (business.get('name', '').lower(), business.get('address', '').lower())
            if key not in seen and key != ('', ''):
                seen.add(key)
                unique_businesses.append(business)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Unique Results", 
            str(Path.home() / "Desktop" / "unique_businesses.csv"),
            "CSV Files (*.csv)"
        )
        
        if file_path:
            self._save_to_csv(unique_businesses, file_path)
            QMessageBox.information(self, "Success", f"Saved {len(unique_businesses)} unique businesses to {file_path}")
            
    def _save_to_csv(self, businesses, file_path):
        """Save businesses to CSV file"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['keyword', 'name', 'address', 'phone', 'website', 'rating', 'reviews', 'category']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for business in businesses:
                    writer.writerow(business)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")
            
    def clear_results(self):
        """Clear all results"""
        self.scraped_businesses = []
        self.results_table.setRowCount(0)
        self.progress_log.clear()
        self.total_businesses = 0
        self.unique_businesses = 0
        self.update_stats()
        
        # Reset dashboard
        if hasattr(self, 'total_businesses_card'):
            total_value = self.total_businesses_card.findChild(QLabel, "statValue")
            unique_value = self.unique_businesses_card.findChild(QLabel, "statValue")
            success_value = self.success_rate_card.findChild(QLabel, "statValue")
            keyword_value = self.current_keyword_card.findChild(QLabel, "statValue")
            processed_value = self.keywords_processed_card.findChild(QLabel, "statValue")
            status_value = self.scraping_status_card.findChild(QLabel, "statValue")
            
            if total_value: total_value.setText("0")
            if unique_value: unique_value.setText("0")
            if success_value: success_value.setText("0%")
            if keyword_value: keyword_value.setText("Ready")
            if processed_value: processed_value.setText("0")
            if status_value: status_value.setText("⏸️ Idle")
        
        # Reset dashboard progress and activity
        if hasattr(self, 'dashboard_progress_bar'):
            self.dashboard_progress_bar.setValue(0)
            self.dashboard_progress_bar.setFormat("Ready to start scraping...")
        
        if hasattr(self, 'dashboard_activity_log'):
            self.dashboard_activity_log.clear()
            self.dashboard_activity_log.append("[Dashboard] Ready to start scraping...")
        
        self.log_progress("🗑️ Results cleared")
        
    def log_progress(self, message: str):
        """Log progress message"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.progress_log.append(formatted_message)
        self.status_bar.showMessage(message)
        
    def add_business_to_table(self, business_data: dict):
        """Add business to the results table"""
        self.scraped_businesses.append(business_data)
        
        # Add to table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        columns = ["keyword", "name", "website", "phone", "address", "rating", "category"]
        
        for col, field in enumerate(columns):
            item = QTableWidgetItem(str(business_data.get(field, '')))
            self.results_table.setItem(row, col, item)
        
        # Update stats
        self.total_businesses = len(self.scraped_businesses)
        
        # Calculate unique businesses
        seen = set()
        unique_count = 0
        for business in self.scraped_businesses:
            key = (business.get('name', '').lower(), business.get('address', '').lower())
            if key not in seen and key != ('', ''):
                seen.add(key)
                unique_count += 1
        
        self.unique_businesses = unique_count
        self.update_stats()
        
    def update_stats(self):
        """Update statistics display"""
        pass
    
    def update_dashboard_activity(self, message: str):
        """Update dashboard activity log"""
        if hasattr(self, 'dashboard_activity_log'):
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.dashboard_activity_log.append(formatted_message)
            # Keep only last 50 messages for performance
            if self.dashboard_activity_log.document().blockCount() > 50:
                cursor = self.dashboard_activity_log.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.select(cursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deletePreviousChar()  # Remove the newline
    
    def update_dashboard_stats(self, business_data: dict):
        """Update dashboard statistics when a new business is found"""
        if hasattr(self, 'total_businesses_card'):
            # Find the value labels in the stat cards
            total_value = self.total_businesses_card.findChild(QLabel, "statValue")
            unique_value = self.unique_businesses_card.findChild(QLabel, "statValue")
            success_value = self.success_rate_card.findChild(QLabel, "statValue")
            
            if total_value:
                total_value.setText(str(self.total_businesses))
            if unique_value:
                unique_value.setText(str(self.unique_businesses))
            if success_value and self.total_businesses > 0:
                success_rate = (self.unique_businesses / self.total_businesses) * 100
                success_value.setText(f"{success_rate:.1f}%")
            
            # Update progress bar
            if hasattr(self, 'scraping_thread') and self.scraping_thread:
                total_keywords = len(self.scraping_thread.keywords)
                # Estimate progress based on current activity
                current_progress = min(95, (self.total_businesses / max(1, total_keywords * 10)) * 100)
                self.dashboard_progress_bar.setValue(int(current_progress))
                self.dashboard_progress_bar.setFormat(f"Processing... {self.total_businesses} businesses found")
    
    def update_dashboard_keyword(self, keyword: str):
        """Update dashboard with current keyword being processed"""
        if hasattr(self, 'current_keyword_card'):
            # Find the value label in the current keyword card
            keyword_value = self.current_keyword_card.findChild(QLabel, "statValue")
            if keyword_value:
                keyword_value.setText(keyword)
            
            # Update keywords processed count
            if hasattr(self, 'scraping_thread') and self.scraping_thread:
                current_index = self.scraping_thread.keywords.index(keyword) + 1 if keyword in self.scraping_thread.keywords else 0
                total_keywords = len(self.scraping_thread.keywords)
                
                processed_value = self.keywords_processed_card.findChild(QLabel, "statValue")
                if processed_value:
                    processed_value.setText(f"{current_index}/{total_keywords}")
                
                # Update progress bar
                progress = (current_index / total_keywords) * 100 if total_keywords > 0 else 0
                self.dashboard_progress_bar.setValue(int(progress))
                self.dashboard_progress_bar.setFormat(f"Processing: {keyword}")
                
                # Update status
                status_value = self.scraping_status_card.findChild(QLabel, "statValue")
                if status_value:
                    status_value.setText("🔄 Scraping")
        
    def update_current_keyword(self, keyword: str):
        """Update the current keyword display"""
        pass
        
    def scraping_finished(self, result_count):
        """Handle scraping completion"""
        self.log_progress(f"🎉 Scraping completed! Total businesses found: {result_count}")
        
        # Update dashboard status to completed
        if hasattr(self, 'scraping_status_card'):
            status_value = self.scraping_status_card.findChild(QLabel, "statValue")
            if status_value:
                status_value.setText("✅ Complete")
        
        # Update progress bar to 100%
        if hasattr(self, 'dashboard_progress_bar'):
            self.dashboard_progress_bar.setValue(100)
            self.dashboard_progress_bar.setFormat(f"Completed! {result_count} businesses found")
        
        # Add completion message to dashboard activity
        if hasattr(self, 'dashboard_activity_log'):
            timestamp = time.strftime("%H:%M:%S")
            self.dashboard_activity_log.append(f"[{timestamp}] 🎉 Scraping completed! Found {result_count} businesses")
        
        # Reset button states
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        if result_count > 0:
            QMessageBox.information(
                self, "Scraping Complete",
                f"Successfully scraped {result_count} business listings!\n\n"
                f"Total: {self.total_businesses}\n"
                f"Unique: {self.unique_businesses}"
            )