# clipboard_handler.py

import os
import uuid
import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QBuffer, QIODevice
from typing import Optional, Tuple

class ClipboardImageHandler:
    def __init__(self, base_dir=None):
        """
        Initialize clipboard handler with optional base directory.
        If no base_dir provided, uses current working directory.
        """
        #self.base_dir = base_dir or os.getcwd()
        #self.images_folder = "images"
        #self.ensure_images_folder()

        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = os.path.abspath(os.path.dirname(sys.modules['__main__'].__file__))
            
        self.images_folder = "images"
        self.ensure_images_folder()
    
    def ensure_images_folder(self):
        """Create images folder if it doesn't exist"""
        images_path = os.path.join(self.base_dir, self.images_folder)
        try:
            os.makedirs(images_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating images folder: {e}")
            return False
    
    def generate_unique_filename(self) -> str:
        """Generate unique filename using timestamp and UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"img_{timestamp}_{unique_id}.png"
    
    def get_clipboard_image(self) -> Optional[QImage]:
        """Get image from clipboard if available"""
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                image = clipboard.image()
                if not image.isNull():
                    return image
            
            # Try to get pixmap if image failed
            pixmap = clipboard.pixmap()
            if not pixmap.isNull():
                return pixmap.toImage()
                
        except Exception as e:
            print(f"Error getting clipboard image: {e}")
        
        return None
    
    def save_image_to_file(self, image: QImage, filename: str) -> Tuple[bool, str]:
        """
        Save QImage to file in images folder.
        Returns (success, full_path)
        """
        try:
            full_path = os.path.join(self.base_dir, self.images_folder, filename)
            
            # Convert to PNG format with best quality
            success = image.save(full_path, "PNG", 100)
            
            if success:
                return True, full_path
            else:
                return False, ""
                
        except Exception as e:
            print(f"Error saving image: {e}")
            return False, ""
    
    def process_clipboard_image(self) -> Optional[Tuple[str, str]]:
        """
        Process image from clipboard: get, save, and return paths.
        Returns (relative_path, absolute_path) or None if failed
        """
        # Get image from clipboard
        image = self.get_clipboard_image()
        if image is None:
            return None
        
        # Generate unique filename
        filename = self.generate_unique_filename()
        
        # Save image to file
        success, full_path = self.save_image_to_file(image, filename)
        
        if success:
            # Return relative path for markdown and full path for reference
            relative_path = f"{self.images_folder}/{filename}"
            return relative_path, full_path
        
        return None
    
    def create_markdown_image_link(self, alt_text: str, relative_path: str) -> str:
        """Create markdown image link"""
        # Sanitize alt text
        alt_text = alt_text.replace('"', '\\"').replace('\n', ' ').strip()
        if not alt_text:
            alt_text = "Pasted Image"
        
        return f"![{alt_text}]({relative_path})"
    
    def has_image_in_clipboard(self) -> bool:
        """Check if clipboard contains an image"""
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            return mime_data.hasImage() or not clipboard.pixmap().isNull()
            
        except Exception:
            return False