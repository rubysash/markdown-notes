# utils.py

from PyQt5.QtWidgets import (QInputDialog, QMessageBox, QDialog, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QCheckBox, QProgressBar,
                            QTextEdit, QGroupBox)
#from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import Tuple
import os
import file_manager

# Utility Functions
def prompt_input(title, prompt):
    text, ok = QInputDialog.getText(None, title, prompt)
    return text if ok else None

def confirm(title, prompt):
    reply = QMessageBox.question(None, title, prompt, QMessageBox.Yes | QMessageBox.No)
    return reply == QMessageBox.Yes

def confirm_move_operation(source_path: str, dest_path: str, parent=None) -> Tuple[bool, bool]:
    """
    Show move confirmation dialog.
    Returns: (proceed, verify_integrity)
    """
    dialog = MoveConfirmationDialog(source_path, dest_path, parent)
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return True, dialog.verify_integrity
    else:
        return False, False

class MoveConfirmationDialog(QDialog):
    def __init__(self, source_path: str, dest_path: str, parent=None):
        super().__init__(parent)
        self.source_path = source_path
        self.dest_path = dest_path
        self.verify_integrity = True  # Default to True
        self.result_action = None
        
        self.setWindowTitle("Confirm Move Operation")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        self.analyze_operation()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Operation details
        details_group = QGroupBox("Operation Details")
        details_layout = QVBoxLayout()
        
        self.source_label = QLabel(f"Source: {self.source_path}")
        self.dest_label = QLabel(f"Destination: {self.dest_path}")
        self.cross_drive_label = QLabel("")
        self.stats_label = QLabel("Analyzing...")
        
        details_layout.addWidget(self.source_label)
        details_layout.addWidget(self.dest_label)
        details_layout.addWidget(self.cross_drive_label)
        details_layout.addWidget(self.stats_label)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Verification options
        verify_group = QGroupBox("Verification Options")
        verify_layout = QVBoxLayout()
        
        self.verify_checkbox = QCheckBox("Verify file integrity with MD5 checksums (Recommended)")
        self.verify_checkbox.setChecked(True)
        self.verify_checkbox.stateChanged.connect(self.on_verify_changed)
        verify_layout.addWidget(self.verify_checkbox)
        
        self.verify_info = QLabel("MD5 verification ensures files are copied correctly and prevents data corruption.")
        self.verify_info.setWordWrap(True)
        self.verify_info.setStyleSheet("color: #888; font-size: 11px;")
        verify_layout.addWidget(self.verify_info)
        
        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)
        
        # Warnings/Info area
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        layout.addWidget(self.info_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.proceed_btn = QPushButton("Proceed with Move")
        self.proceed_btn.clicked.connect(self.accept)
        self.proceed_btn.setDefault(True)  # Default button for Enter key
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.proceed_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def analyze_operation(self):
        try:
            # Check if cross-drive
            is_cross_drive = file_manager.check_cross_drive_operation(self.source_path, self.dest_path)
            
            if is_cross_drive:
                self.cross_drive_label.setText("⚠️ Cross-drive operation detected")
                self.cross_drive_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.cross_drive_label.setText("✓ Same-drive operation")
                self.cross_drive_label.setStyleSheet("color: green;")
            
            # Get file statistics
            file_count, total_size = file_manager.get_directory_stats(self.source_path)
            size_mb = total_size / (1024 * 1024)
            
            self.stats_label.setText(f"Files: {file_count:,} | Size: {size_mb:.1f} MB")
            
            # Check permissions
            dest_dir = os.path.dirname(self.dest_path)
            perm_ok, perm_msg = file_manager.check_permissions(self.source_path, dest_dir)
            
            # Generate warnings and recommendations
            warnings = []
            
            if not perm_ok:
                warnings.append(f"Permission Error: {perm_msg}")
                self.proceed_btn.setEnabled(False)
            
            if is_cross_drive:
                warnings.append("Cross-drive operations are slower and more prone to corruption.")
                warnings.append("MD5 verification is strongly recommended for data safety.")
            
            if file_count > 1000:
                warnings.append(f"Large operation: {file_count:,} files may take significant time.")
            
            if size_mb > 1000:
                warnings.append(f"Large data transfer: {size_mb:.1f} MB will take time to verify.")
            
            if file_count > 100 or size_mb > 100:
                warnings.append("Progress dialog will show detailed status during operation.")
            
            if not warnings:
                warnings.append("✓ Operation appears safe to proceed.")
            
            self.info_text.setPlainText("\n".join(warnings))
            
        except Exception as e:
            self.stats_label.setText(f"Analysis failed: {str(e)}")
            self.info_text.setPlainText(f"Could not analyze operation: {str(e)}")
    
    def on_verify_changed(self, state):
        self.verify_integrity = state == Qt.Checked
        if not self.verify_integrity:
            self.verify_info.setText("⚠️ Disabling verification increases risk of undetected corruption.")
            self.verify_info.setStyleSheet("color: orange; font-size: 11px;")
        else:
            self.verify_info.setText("MD5 verification ensures files are copied correctly and prevents data corruption.")
            self.verify_info.setStyleSheet("color: #888; font-size: 11px;")
'''
class MoveProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Moving Files...")
        self.setModal(True)
        self.resize(600, 300)
        self.cancelled = False
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Overall progress
        self.overall_label = QLabel("Preparing move operation...")
        layout.addWidget(self.overall_label)
        
        self.overall_progress = QProgressBar()
        layout.addWidget(self.overall_progress)
        
        # Current file
        self.current_label = QLabel("")
        layout.addWidget(self.current_label)
        
        self.current_progress = QProgressBar()
        layout.addWidget(self.current_progress)
        
        # Status information
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_operation)
        
        self.background_btn = QPushButton("Run in Background")
        self.background_btn.clicked.connect(self.run_in_background)
        self.background_btn.setEnabled(False)  # Enable after move starts
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.background_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def update_overall_progress(self, current: int, total: int, status: str = ""):
        self.overall_progress.setMaximum(total)
        self.overall_progress.setValue(current)
        if status:
            self.overall_label.setText(f"{status} ({current}/{total})")
    
    def update_current_file(self, filename: str, stage: str = ""):
        display_name = os.path.basename(filename) if filename else ""
        if stage:
            self.current_label.setText(f"{stage}: {display_name}")
        else:
            self.current_label.setText(display_name)
    
    def update_current_progress(self, current: int, total: int):
        self.current_progress.setMaximum(total)
        self.current_progress.setValue(current)
    
    def add_status_message(self, message: str):
        self.status_text.append(message)
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.End)
        self.status_text.setTextCursor(cursor)
    
    def cancel_operation(self):
        self.cancelled = True
        self.cancel_btn.setText("Cancelling...")
        self.cancel_btn.setEnabled(False)
    
    def run_in_background(self):
        self.hide()
    
    def enable_background_option(self):
        self.background_btn.setEnabled(True)
'''