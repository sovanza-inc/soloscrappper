from typing import TYPE_CHECKING

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QLineEdit, QMessageBox
    )
    from PyQt5.QtCore import Qt, QTimer
except ImportError:
    print("PyQt5 is not installed. Please install it using:")
    print("pip install PyQt5")
    raise ImportError("PyQt5 is required for the license dialog")

if TYPE_CHECKING:
    from .manager import LicenseManager
else:
    from .manager import LicenseManager


class LicenseDialog(QDialog):
    """License key input dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.setup_ui()
        self.setModal(True)
    
    def setup_ui(self):
        """Setup the license dialog UI"""
        self.setWindowTitle("License Activation")
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Solo Scrapper Pro - License Activation")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                margin: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Machine ID display
        machine_id_label = QLabel(f"Machine ID: {self.license_manager.get_machine_id()}")
        machine_id_label.setAlignment(Qt.AlignCenter)
        machine_id_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cccccc;
                margin: 5px;
                padding: 5px;
                background-color: #2d2d2d;
                border-radius: 5px;
            }
        """)
        layout.addWidget(machine_id_label)
        
        # License key input
        license_label = QLabel("Enter License Key:")
        license_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #ffffff;
                margin-top: 20px;
            }
        """)
        layout.addWidget(license_label)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter your license key here...")
        self.license_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 10px;
                border: 2px solid #555555;
                border-radius: 5px;
                background-color: #2d2d2d;
                color: #ffffff;
                margin: 5px 0;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.license_input)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                margin: 10px;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Validate License")
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.validate_btn.clicked.connect(self.validate_license)
        button_layout.addWidget(self.validate_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
    
    def validate_license(self):
        """Validate the entered license key"""
        license_key = self.license_input.text().strip()
        
        if not license_key:
            self.show_status("Please enter a license key", "error")
            return
        
        # Show loading state
        self.show_loading_state(True)
        
        # Use QTimer to allow UI to update before validation
        QTimer.singleShot(100, lambda: self.perform_validation(license_key))
    
    def show_loading_state(self, loading: bool):
        """Show or hide loading state"""
        if loading:
            # Disable input and button
            self.license_input.setEnabled(False)
            self.validate_btn.setEnabled(False)
            self.validate_btn.setText("🔄 Validating...")
            
            # Show loading message
            self.show_status("🔄 Connecting to license server...", "loading")
            
            # Start loading animation timer
            self.loading_timer = QTimer()
            self.loading_dots = 0
            self.loading_timer.timeout.connect(self.update_loading_animation)
            self.loading_timer.start(500)  # Update every 500ms
        else:
            # Stop loading animation
            if hasattr(self, 'loading_timer'):
                self.loading_timer.stop()
            
            # Re-enable input and button
            self.license_input.setEnabled(True)
            self.validate_btn.setEnabled(True)
            self.validate_btn.setText("Validate License")
    
    def update_loading_animation(self):
        """Update loading animation dots"""
        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.show_status(f"🔄 Connecting to license server{dots}", "loading")
    
    def perform_validation(self, license_key: str):
        """Perform the actual license validation"""
        # Validate license
        is_valid, message = self.license_manager.validate_license(license_key)
        
        # Hide loading state
        self.show_loading_state(False)
        
        if is_valid:
            self.show_status(message, "success")
            QTimer.singleShot(1500, self.accept)  # Close dialog after 1.5 seconds
        else:
            self.show_status(message, "error")
    
    def show_status(self, message: str, status_type: str):
        """Show status message with appropriate styling"""
        self.status_label.setText(message)
        
        if status_type == "success":
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    margin: 10px;
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #4CAF50;
                    color: white;
                }
            """)
        elif status_type == "error":
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    margin: 10px;
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #f44336;
                    color: white;
                }
            """)
        elif status_type == "loading":
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    margin: 10px;
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #2196F3;
                    color: white;
                }
            """)