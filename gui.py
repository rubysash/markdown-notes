# gui.py

import os
import platform
from PyQt5.QtWidgets import (
    QMainWindow, QTreeWidget, QTreeWidgetItem, QSplitter, QWidget,
    QVBoxLayout, QPlainTextEdit, QMessageBox, QTabWidget, QPushButton, 
    QInputDialog, QMessageBox, QShortcut, QMenu
)

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence, QDrag
from PyQt5.QtCore import QMimeData
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QHBoxLayout, QInputDialog

from clipboard_handler import ClipboardImageHandler

import file_manager
import render

class MarkdownManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Note Taker - v17")

        # Initialize config manager
        from config import ConfigManager
        self.config_manager = ConfigManager()

        # Initialize clipboard handler
        self.clipboard_handler = ClipboardImageHandler()

        # Track unsaved changes
        self.has_unsaved_changes = False

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Left panel layout
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        self.tree = MarkdownTreeWidget(self)
        self.tree.setHeaderHidden(True)
        left_layout.addWidget(self.tree)

        # Connect the custom signal to refresh tree
        self.tree.tree_updated.connect(lambda: self.load_tree("."))

        # Add context menu to tree
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Save button - Full width at bottom of left panel
        self.save_file_btn = QPushButton("Save File (Ctrl+S)")
        self.save_file_btn.clicked.connect(self.save_current_file)
        self.update_save_button_style()
        left_layout.addWidget(self.save_file_btn)

        # Refresh Tree button and Print button - Same row
        refresh_print_row = QWidget()
        refresh_print_layout = QHBoxLayout()
        refresh_print_row.setLayout(refresh_print_layout)

        self.refresh_tree_btn = QPushButton("Refresh Tree")
        self.refresh_tree_btn.clicked.connect(self.refresh_tree_preserve_state)
        self.refresh_tree_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: #f0f0f0;
                border: 1px solid #333;
                padding: 8px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)
        refresh_print_layout.addWidget(self.refresh_tree_btn)

        self.print_btn = QPushButton("Print Preview")
        self.print_btn.clicked.connect(self.print_preview)
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: #f0f0f0;
                border: 1px solid #333;
                padding: 8px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        refresh_print_layout.addWidget(self.print_btn)

        left_layout.addWidget(refresh_print_row)

        # Add special function buttons at bottom
        special_button_row = QWidget()
        special_layout = QHBoxLayout()
        special_button_row.setLayout(special_layout)
        
        front_matter_btn = QPushButton("Add Front Matter")
        front_matter_btn.clicked.connect(self.add_front_matter)
        special_layout.addWidget(front_matter_btn)
        
        default_style_btn = QPushButton("Reset Style")
        default_style_btn.clicked.connect(self.reset_default_style)
        special_layout.addWidget(default_style_btn)
        
        left_layout.addWidget(special_button_row)

        # Add image paste button row
        image_button_row = QWidget()
        image_layout = QHBoxLayout()
        image_button_row.setLayout(image_layout)
        
        paste_image_btn = QPushButton("Paste Image (Ctrl+Shift+V)")
        paste_image_btn.clicked.connect(self.paste_image_from_clipboard)
        paste_image_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: #f0f0f0;
                border: 1px solid #333;
                padding: 8px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        image_layout.addWidget(paste_image_btn)
        
        left_layout.addWidget(image_button_row)

        # Keybinds
        # Keyboard shortcut for save
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_current_file)

        # F2 for renaming selected file or folder
        rename_shortcut = QShortcut(QKeySequence(Qt.Key_F2), self)
        rename_shortcut.activated.connect(self.handle_rename_shortcut)

        # Ctrl+N for creating new file in current directory
        new_file_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_file_shortcut.activated.connect(self.handle_new_file_shortcut)

        # Ctrl+Shift+V for pasting images from clipboard
        paste_image_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        paste_image_shortcut.activated.connect(self.paste_image_from_clipboard)

        splitter.addWidget(left_panel)
        self.load_tree(".")

        # Right panel - Tab widget
        self.tab_widget = QTabWidget()
        splitter.addWidget(self.tab_widget)

        # Editor tab
        self.editor = QPlainTextEdit()
        editor_font = QFont()
        editor_font.setFamily("Courier New")
        editor_font.setFixedPitch(True)
        editor_font.setStyleHint(QFont.Monospace)
        self.editor.setFont(editor_font)
        self.editor.setStyleSheet("font-family: 'Courier New', monospace;")
        self.tab_widget.addTab(self.editor, "Editor")

        # Preview tab
        self.render_html = QWebEngineView()
        self.tab_widget.addTab(self.render_html, "Preview")

        # Style tab
        self.style_editor = QPlainTextEdit()
        style_font = QFont()
        style_font.setFamily("Courier New")
        style_font.setFixedPitch(True)
        style_font.setStyleHint(QFont.Monospace)
        self.style_editor.setFont(style_font)
        self.style_editor.setStyleSheet("font-family: 'Courier New', monospace;")
        
        # Load initial style configuration
        config_content = self.config_manager.load_config()
        self.style_editor.setPlainText(config_content)
        
        self.tab_widget.addTab(self.style_editor, "Style")

        self.current_file = None
        self.original_content = ""

        self.tree.itemClicked.connect(self.load_file_to_editor)
        self.editor.textChanged.connect(self.on_editor_text_changed)
        self.style_editor.textChanged.connect(self.update_rendered_view)
        self.tab_widget.currentChanged.connect(self.handle_tab_change)

        # Set proportional sizes: 25% for left panel, 75% for right panel
        splitter.setSizes([250, 750])
        
        # Enable collapsible splitter with minimum sizes to prevent complete collapse
        splitter.setChildrenCollapsible(True)
        left_panel.setMinimumSize(150, 0)
        self.tab_widget.setMinimumSize(300, 0)

    def handle_paste_event(self):
        """Handle paste event for images and text"""
        try:
            # Check if clipboard contains an image
            if self.clipboard_handler.has_image_in_clipboard():
                # Process the image
                result = self.clipboard_handler.process_clipboard_image()
                
                if result:
                    relative_path, full_path = result
                    
                    # Get cursor position
                    cursor = self.editor.textCursor()
                    
                    # Ask for alt text (optional)
                    from PyQt5.QtWidgets import QInputDialog
                    alt_text, ok = QInputDialog.getText(
                        self, 
                        "Image Description", 
                        "Enter alt text for the image (optional):",
                        text="Image"
                    )
                    
                    if not ok:
                        alt_text = "Image"
                    
                    # Create markdown link
                    markdown_link = self.clipboard_handler.create_markdown_image_link(
                        alt_text, 
                        relative_path
                    )
                    
                    # Insert at cursor position
                    cursor.insertText(markdown_link)
                    
                    # Update preview
                    self.update_rendered_view()
                    
                    # Show success message
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self, 
                        "Image Pasted", 
                        f"Image saved to: {relative_path}"
                    )
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self, 
                        "Paste Failed", 
                        "Failed to save image from clipboard"
                    )
            else:
                # Let default paste behavior handle text
                self.editor.paste()
                
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Paste Error", 
                f"Error during paste operation: {str(e)}"
            )
    
    def keyPressEvent(self, event):
        """Override key press event to handle Ctrl+V"""
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QKeySequence
        
        # Check if Ctrl+V is pressed and editor has focus
        if (event.matches(QKeySequence.Paste) and 
            self.editor.hasFocus()):
            self.handle_paste_event()
        else:
            # Pass to parent for default handling
            super().keyPressEvent(event)

    def handle_rename_shortcut(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a file or folder to rename.")
            return

        selected_path = self.get_full_path(selected_item)
        if not selected_path or not os.path.exists(selected_path):
            QMessageBox.warning(self, "Invalid Selection", "Selected item does not exist.")
            return

        if not (os.path.isdir(selected_path) or (os.path.isfile(selected_path) and selected_path.endswith(".md"))):
            QMessageBox.warning(self, "Invalid Selection", "Please select a .md file or a folder to rename.")
            return

        self.rename_selected_item()

    def handle_new_file_shortcut(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a folder or file to determine the target directory.")
            return

        selected_path = self.get_full_path(selected_item)
        if not selected_path or not os.path.exists(selected_path):
            QMessageBox.warning(self, "Invalid Selection", "Selected item does not exist.")
            return

        target_path = selected_path if os.path.isdir(selected_path) else os.path.dirname(selected_path)
        self.create_new_md_file_in_path(target_path)

    def sanitize_filename(self, filename):
        import re
        if not filename:
            return ""
        
        # Only allow alphanumeric characters, periods, hyphens, underscores, and spaces
        # This specifically allows only ASCII space (32), not tabs, newlines, etc.
        sanitized = re.sub(r'[^A-Za-z0-9._\- ]', '', filename)
        
        # Replace multiple consecutive spaces with a single space
        sanitized = re.sub(r' {2,}', ' ', sanitized)
        
        # Remove leading/trailing spaces, periods and hyphens
        sanitized = sanitized.strip(' .-')
        
        # Ensure it doesn't start with a period (hidden file)
        while sanitized.startswith('.'):
            sanitized = sanitized[1:]
        
        # Remove consecutive special characters for cleaner names
        sanitized = re.sub(r'[._-]{2,}', '_', sanitized)
        
        # Limit length to reasonable filesystem limits
        if len(sanitized) > 64:
            sanitized = sanitized[:64].strip(' .-_')
        
        # Check for reserved names (Windows and some Unix systems)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 
            'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 
            'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        # Check base name without extension
        base_name = sanitized.split('.')[0].upper()
        if base_name in reserved_names:
            sanitized = f"file_{sanitized}"
        
        # Ensure we have at least one character
        if not sanitized:
            return ""
        
        return sanitized

    def rename_selected_item(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Error", "No item selected.")
            return

        current_path = self.get_full_path(selected_item)
        if not current_path or not os.path.exists(current_path):
            QMessageBox.warning(self, "Error", "Selected item does not exist.")
            return

        is_directory = os.path.isdir(current_path)
        is_md_file = os.path.isfile(current_path) and current_path.endswith(".md")
        
        if not is_directory and not is_md_file:
            QMessageBox.warning(self, "Error", "Only .md files and folders can be renamed.")
            return

        current_name = os.path.basename(current_path)
        if is_md_file:
            display_name = current_name[:-3]  # Remove .md extension for display
        else:
            display_name = current_name

        item_type = "folder" if is_directory else "file"
        new_name, ok = QInputDialog.getText(
            self, f"Rename {item_type.title()}", 
            f"Enter new name for {item_type}:", 
            text=display_name
        )
        
        if not ok or not new_name or new_name.strip() == "":
            return
        
        # Sanitize the new name
        sanitized_name = self.sanitize_filename(new_name.strip())
        if not sanitized_name:
            QMessageBox.warning(self, "Error", "Invalid name. Please use only letters, numbers, spaces, hyphens, and underscores.")
            return
        
        # Show warning if name was modified
        if sanitized_name != new_name.strip():
            reply = QMessageBox.question(
                self, "Name Modified", 
                f"Name was modified for safety:\nOriginal: {new_name}\nSanitized: {sanitized_name}\n\nProceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Add .md extension back for files
        if is_md_file and not sanitized_name.endswith(".md"):
            sanitized_name += ".md"
        
        if sanitized_name == current_name:
            return  # No change needed
        
        parent_dir = os.path.dirname(current_path)
        new_path = os.path.join(parent_dir, sanitized_name)
        
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Error", f"A {item_type} with this name already exists.")
            return
        
        try:
            expanded_paths = self.tree.get_expanded_paths()
            
            file_manager.rename_item(current_path, new_path)
            
            if self.current_file == current_path:
                self.current_file = new_path
            
            refresh_success = self.tree.refresh_directory_node(parent_dir)
            
            if refresh_success:
                self.tree.restore_expanded_state(expanded_paths)
                renamed_item = self.tree.find_item_by_path(new_path)
                if renamed_item:
                    self.tree.setCurrentItem(renamed_item)
                    self.tree.scrollToItem(renamed_item)
            else:
                print(f"Selective refresh failed for {parent_dir}, falling back to full refresh")
                self.load_tree(".")
            
            QMessageBox.information(self, "Success", f"{item_type.title()} renamed successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rename {item_type}:\n{str(e)}")

    def on_editor_text_changed(self):
            current_content = self.editor.toPlainText()
            self.has_unsaved_changes = (current_content != self.original_content)
            self.update_save_button_style()
            self.update_rendered_view()

    def update_save_button_style(self):
            if self.has_unsaved_changes:
                self.save_file_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff8c00;
                        border: 1px solid #333;
                        padding: 8px 12px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ffa500;
                    }
                    QPushButton:pressed {
                        background-color: #ff7700;
                    }
                """)
            else:
                self.save_file_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #90EE90;
                        color: #000000;
                        border: 1px solid #333;
                        padding: 8px 12px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #98FB98;
                    }
                    QPushButton:pressed {
                        background-color: #87CEEB;
                    }
                """)

    def reset_refresh_button(self):
        """Reset the refresh button to its normal state"""
        self.refresh_tree_btn.setText("Refresh Tree")
        self.refresh_tree_btn.setEnabled(True)

    def print_preview(self):
        """Generate HTML and open in default browser for printing"""
        try:
            # Check if an .md file is currently selected
            if not self.current_file:
                QMessageBox.warning(
                    self, 
                    "No Document Selected", 
                    "Please select a markdown (.md) file before printing."
                )
                return
            
            # Verify the current file is actually a .md file
            if not self.current_file.endswith('.md'):
                QMessageBox.warning(
                    self, 
                    "Invalid File Type", 
                    "Only markdown (.md) files can be printed."
                )
                return
            
            # Get markdown content
            md_text = self.editor.toPlainText()
            if not md_text.strip():
                QMessageBox.warning(
                    self, 
                    "Empty Document", 
                    "The document appears to be empty. Nothing to print."
                )
                return
            
            try:
                # Get print CSS from config manager
                print_css = self.config_manager.load_print_css()
                
                # Generate HTML with print CSS
                import render
                html_content = render.markdown_to_html_for_browser_print(md_text, print_css, self.current_file)
                
                # Create HTML file in same directory as the markdown file
                file_dir = os.path.dirname(os.path.abspath(self.current_file))
                filename_base = os.path.splitext(os.path.basename(self.current_file))[0]
                html_filename = f"{filename_base}_print.html"
                html_filepath = os.path.join(file_dir, html_filename)
                
                # Write HTML file
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Open in default browser
                import webbrowser
                file_url = f"file:///{html_filepath.replace(os.sep, '/')}"
                webbrowser.open(file_url)
                
                # Show success message with instructions
                QMessageBox.information(
                    self, 
                    "Print File Created", 
                    f"Print-ready HTML file created:\n{html_filename}\n\n"
                    f"The file has been opened in your default browser.\n"
                    f"Use Ctrl+P (or Cmd+P on Mac) to print from the browser.\n\n"
                    f"The HTML file will remain in the same folder as your markdown file."
                )
                
            except Exception as render_error:
                QMessageBox.critical(
                    self, 
                    "Print Generation Error", 
                    f"Failed to generate print file:\n{str(render_error)}"
                )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Unexpected Error", 
                f"An unexpected error occurred:\n{str(e)}"
            )

    def paste_image_from_clipboard(self):
        """Handle pasting image from clipboard into markdown"""
        try:
            # Check if we have a file open
            if not self.current_file:
                QMessageBox.warning(
                    self, 
                    "No File Open", 
                    "Please open a markdown file before pasting an image."
                )
                return
            
            # Check if clipboard has an image
            if not self.clipboard_handler.has_image_in_clipboard():
                QMessageBox.information(
                    self, 
                    "No Image", 
                    "No image found in clipboard.\nCopy an image first, then use Ctrl+Shift+V to paste."
                )
                return
            
            # Set the base directory to the application root (where app.py is)
            #app_root_dir = os.path.abspath(os.path.dirname(__file__))
            #self.clipboard_handler.base_dir = app_root_dir
            self.clipboard_handler.ensure_images_folder()
            app_root_dir = self.clipboard_handler.base_dir  # added 
            
            # Process the clipboard image
            result = self.clipboard_handler.process_clipboard_image()
            
            if result:
                relative_path, absolute_path = result
                
                # Ask user for alt text
                alt_text, ok = QInputDialog.getText(
                    self, 
                    "Image Description", 
                    "Enter alt text for the image (optional):",
                    text="Pasted Image"
                )
                
                if not ok:
                    alt_text = "Pasted Image"
                
                # Calculate relative path from current markdown file to root images folder
                current_file_dir = os.path.dirname(os.path.abspath(self.current_file))
                
                # Get relative path from current file to app root
                try:
                    rel_path_to_root = os.path.relpath(app_root_dir, current_file_dir)

                    # Normalize path separators for markdown
                    rel_path_to_root = rel_path_to_root.replace(os.sep, '/')
                    
                    # Build the markdown image path
                    '''
                    if rel_path_to_root == '.':
                        # Same directory as app root
                        markdown_image_path = relative_path
                    else:
                        # Need to navigate to root first
                        markdown_image_path = f"{rel_path_to_root}/{relative_path}"
                        # Clean up any redundant slashes or dots
                        markdown_image_path = markdown_image_path.replace('//', '/')
                    '''
                    markdown_image_path = f"/{relative_path}".replace('//', '/')
                except ValueError:
                    # Different drives on Windows, use absolute path from root
                    markdown_image_path = f"/{relative_path}"
                
                # Create markdown link
                markdown_link = self.clipboard_handler.create_markdown_image_link(
                    alt_text, 
                    markdown_image_path
                )
                
                # Insert into editor at cursor position
                cursor = self.editor.textCursor()
                
                # Add newlines if needed
                current_text = self.editor.toPlainText()
                cursor_pos = cursor.position()
                
                # Check if we need newlines before
                if cursor_pos > 0 and current_text[cursor_pos - 1] != '\n':
                    markdown_link = '\n' + markdown_link
                
                # Check if we need newlines after
                if cursor_pos < len(current_text) and current_text[cursor_pos] != '\n':
                    markdown_link = markdown_link + '\n'
                
                # Insert the markdown
                cursor.insertText(markdown_link)
                
                # Update the preview
                self.update_rendered_view()
                
                # Show success message
                filename = os.path.basename(absolute_path)
                QMessageBox.information(
                    self, 
                    "Image Pasted", 
                    f"Image saved as: {filename}\nLocation: images/{filename}\nMarkdown path: {markdown_image_path}"
                )
                
                # Mark as having unsaved changes
                self.has_unsaved_changes = True
                self.update_save_button_style()
                
            else:
                QMessageBox.critical(
                    self, 
                    "Paste Failed", 
                    "Failed to save the image from clipboard.\nPlease try again."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred while pasting the image:\n{str(e)}"
            )

    # Context aware stuff
    def show_context_menu(self, position):
        selected_item = self.tree.itemAt(position)
        menu = QMenu()
        
        if selected_item:
            # Get the path of the selected item
            selected_path = self.get_full_path(selected_item)
            is_directory = os.path.isdir(selected_path) if selected_path else False
            is_md_file = (os.path.isfile(selected_path) and 
                        selected_path.endswith(".md")) if selected_path else False
            
            # Context-aware menu items
            if is_directory:
                # Directory context menu
                menu.addAction("📄 New File in Folder").triggered.connect(
                    lambda: self.create_new_md_file_in_path(selected_path)
                )
                menu.addAction("📂 New Subfolder").triggered.connect(
                    lambda: self.create_new_folder_in_path(selected_path)
                )
                menu.addSeparator()
                menu.addAction("✏️ Rename Folder").triggered.connect(
                    lambda: self.rename_item_by_path(selected_path)
                )
                menu.addAction("🗑️ Delete Folder").triggered.connect(
                    lambda: self.delete_item_by_path(selected_path)
                )
                
            elif is_md_file:
                # Markdown file context menu
                parent_dir = os.path.dirname(selected_path)
                menu.addAction("📖 Open File").triggered.connect(
                    lambda: self.load_file_by_path(selected_path)
                )
                menu.addSeparator()
                menu.addAction("📄 New File in Parent").triggered.connect(
                    lambda: self.create_new_md_file_in_path(parent_dir)
                )
                menu.addAction("📂 New Folder in Parent").triggered.connect(
                    lambda: self.create_new_folder_in_path(parent_dir)
                )
                menu.addSeparator()
                menu.addAction("✏️ Rename File").triggered.connect(
                    lambda: self.rename_item_by_path(selected_path)
                )
                menu.addAction("🗑️ Delete File").triggered.connect(
                    lambda: self.delete_item_by_path(selected_path)
                )
            else:
                # Unknown item type
                menu.addAction("❓ Unknown Item Type").setEnabled(False)
        else:
            # Empty space clicked - root directory operations
            current_root = self.get_current_root_path()
            menu.addAction("📄 New File").triggered.connect(
                lambda: self.create_new_md_file_in_path(current_root)
            )
            menu.addAction("📂 New Folder").triggered.connect(
                lambda: self.create_new_folder_in_path(current_root)
            )
        
        # Show the menu if it has actions
        if menu.actions():
            menu.exec_(self.tree.viewport().mapToGlobal(position))

    def get_current_root_path(self):
        """Get the current root path being displayed in the tree"""
        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            root_path = self.get_full_path(first_item)
            if root_path and os.path.exists(root_path):
                return root_path
        return "."

    def create_new_md_file_in_path(self, target_path):
        """Create a new markdown file in the specified path"""
        if not os.path.isdir(target_path):
            target_path = os.path.dirname(target_path)
        
        filename, ok = QInputDialog.getText(self, "New Markdown File", "Enter file name:")
        if ok and filename:
            # Sanitize filename
            sanitized_name = self.sanitize_filename(filename.strip())
            if not sanitized_name:
                QMessageBox.warning(self, "Error", "Invalid file name. Please use only letters, numbers, periods, hyphens, and underscores.")
                return
            
            # Show warning if name was modified
            if sanitized_name != filename.strip():
                reply = QMessageBox.question(
                    self, "Name Modified", 
                    f"File name was modified for safety:\nOriginal: {filename}\nSanitized: {sanitized_name}\n\nProceed?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Add .md extension if not present
            if not sanitized_name.endswith(".md"):
                sanitized_name += ".md"
                
            new_file_path = os.path.join(target_path, sanitized_name)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Error", "File already exists.")
            else:
                try:
                    # Store complete state
                    expanded_paths = self.tree.get_expanded_paths()
                    current_selection = None
                    if self.tree.currentItem():
                        current_selection = self.get_full_path(self.tree.currentItem())
                    
                    scroll_bar = self.tree.verticalScrollBar()
                    scroll_position = scroll_bar.value()
                    
                    # Create the file
                    file_manager.create_new_file(target_path, sanitized_name)
                    
                    # Refresh and restore state
                    if self.tree.refresh_directory_node(target_path):
                        self.tree.restore_expanded_state(expanded_paths)
                        
                        # Ensure parent is expanded
                        parent_item = self.tree.find_item_by_path(target_path)
                        if parent_item and not parent_item.isExpanded():
                            parent_item.setExpanded(True)
                        
                        # Select and open the new file
                        new_item = self.tree.find_item_by_path(new_file_path)
                        if new_item:
                            self.tree.setCurrentItem(new_item)
                            self.tree.scrollToItem(new_item)
                            # Auto-open the new file
                            self.load_file_by_path(new_file_path)
                        else:
                            # Restore previous state if new item not found
                            if current_selection:
                                selection_item = self.tree.find_item_by_path(current_selection)
                                if selection_item:
                                    self.tree.setCurrentItem(selection_item)
                            scroll_bar.setValue(scroll_position)
                    else:
                        self.load_tree(".")
                        self.tree.restore_expanded_state(expanded_paths)
                        new_item = self.tree.find_item_by_path(new_file_path)
                        if new_item:
                            self.tree.setCurrentItem(new_item)
                            self.tree.scrollToItem(new_item)
                            self.load_file_by_path(new_file_path)
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create file:\n{str(e)}")

    def create_new_folder_in_path(self, target_path):
        """Create a new folder in the specified path"""
        if not os.path.isdir(target_path):
            target_path = os.path.dirname(target_path)
        
        foldername, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and foldername:
            # Sanitize folder name
            sanitized_name = self.sanitize_filename(foldername.strip())
            if not sanitized_name:
                QMessageBox.warning(self, "Error", "Invalid folder name. Please use only letters, numbers, periods, hyphens, and underscores.")
                return
            
            # Show warning if name was modified
            if sanitized_name != foldername.strip():
                reply = QMessageBox.question(
                    self, "Name Modified", 
                    f"Folder name was modified for safety:\nOriginal: {foldername}\nSanitized: {sanitized_name}\n\nProceed?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            new_folder_path = os.path.join(target_path, sanitized_name)
            if os.path.exists(new_folder_path):
                QMessageBox.warning(self, "Error", "Folder already exists.")
            else:
                try:
                    # Store complete state before any operations
                    expanded_paths = self.tree.get_expanded_paths()
                    current_selection = None
                    if self.tree.currentItem():
                        current_selection = self.get_full_path(self.tree.currentItem())
                    
                    # Store scroll position
                    scroll_bar = self.tree.verticalScrollBar()
                    scroll_position = scroll_bar.value()
                    
                    # Create the folder
                    file_manager.create_new_folder(target_path, sanitized_name)
                    
                    # Try selective refresh first
                    refresh_success = self.tree.refresh_directory_node(target_path)
                    
                    if refresh_success:
                        # Restore expanded state for all previously expanded paths
                        self.tree.restore_expanded_state(expanded_paths)
                        
                        # Ensure parent of new folder is expanded
                        parent_item = self.tree.find_item_by_path(target_path)
                        if parent_item and not parent_item.isExpanded():
                            parent_item.setExpanded(True)
                        
                        # Select the newly created folder
                        new_item = self.tree.find_item_by_path(new_folder_path)
                        if new_item:
                            self.tree.setCurrentItem(new_item)
                            self.tree.scrollToItem(new_item)
                        elif current_selection:
                            # Fall back to previous selection if new item not found
                            selection_item = self.tree.find_item_by_path(current_selection)
                            if selection_item:
                                self.tree.setCurrentItem(selection_item)
                        
                        # Restore scroll position if no specific item to scroll to
                        if not new_item:
                            scroll_bar.setValue(scroll_position)
                    else:
                        # Full refresh as fallback
                        self.load_tree(".")
                        # After full refresh, still try to restore state
                        self.tree.restore_expanded_state(expanded_paths)
                        new_item = self.tree.find_item_by_path(new_folder_path)
                        if new_item:
                            self.tree.setCurrentItem(new_item)
                            self.tree.scrollToItem(new_item)
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create folder:\n{str(e)}")

    def rename_item_by_path(self, item_path):
        """Rename an item by its path"""
        # Find the tree item for this path
        item = self.tree.find_item_by_path(item_path)
        if item:
            self.tree.setCurrentItem(item)
            self.rename_selected_item()
        else:
            QMessageBox.warning(self, "Error", "Item not found in tree.")

    def delete_item_by_path(self, item_path):
        """Delete an item by its path"""
        # Find the tree item for this path
        item = self.tree.find_item_by_path(item_path)
        if item:
            self.tree.setCurrentItem(item)
            self.delete_selected()
        else:
            QMessageBox.warning(self, "Error", "Item not found in tree.")

    def load_file_by_path(self, file_path):
        """Load a file by its path"""
        if os.path.isfile(file_path) and file_path.endswith(".md"):
            try:
                content = file_manager.load_file(file_path)
                self.editor.setPlainText(content)
                self.current_file = file_path
                self.original_content = content
                self.has_unsaved_changes = False
                self.update_save_button_style()
                self.update_rendered_view()
                
                # Update window title
                filename = os.path.basename(file_path)
                self.setWindowTitle(f"Markdown Manager - {filename}")
                
                # Select the file in the tree
                file_item = self.tree.find_item_by_path(file_path)
                if file_item:
                    self.tree.setCurrentItem(file_item)
                    self.tree.scrollToItem(file_item)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    # CRUD
    def save_current_file(self):
        """Save the current file or style configuration"""
        # Check which tab is active
        current_tab_index = self.tab_widget.currentIndex()
        
        if current_tab_index == 2:  # Style tab
            self.save_style_config()
            return
        
        if not self.current_file:
            QMessageBox.warning(self, "Error", "No file selected to save.")
            return

        try:
            content = self.editor.toPlainText()
            file_manager.save_file(self.current_file, content)
            self.original_content = content
            self.has_unsaved_changes = False
            self.update_save_button_style()
            QMessageBox.information(self, "Saved", f"File saved:\n{self.current_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")

    def create_new_folder(self):
        selected_item = self.tree.currentItem()
        if selected_item:
            path = self.get_full_path(selected_item)
            if not os.path.isdir(path):
                path = os.path.dirname(path)
        else:
            path = "."

        foldername, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and foldername:
            # Sanitize folder name
            sanitized_name = self.sanitize_filename(foldername.strip())
            if not sanitized_name:
                QMessageBox.warning(self, "Error", "Invalid folder name. Please use only letters, numbers, spaces, hyphens, and underscores.")
                return
            
            if sanitized_name != foldername.strip():
                reply = QMessageBox.question(
                    self, "Name Modified", 
                    f"Folder name was modified for safety:\nOriginal: {foldername}\nSanitized: {sanitized_name}\n\nProceed?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            new_folder_path = os.path.join(path, sanitized_name)
            if os.path.exists(new_folder_path):
                QMessageBox.warning(self, "Error", "Folder already exists.")
            else:
                try:
                    # Capture complete state including scroll position
                    expanded_paths = self.tree.get_expanded_paths()
                    current_selection = None
                    if self.tree.currentItem():
                        current_selection = self.get_full_path(self.tree.currentItem())
                    
                    scroll_bar = self.tree.verticalScrollBar()
                    scroll_position = scroll_bar.value()
                    
                    # Create the folder
                    file_manager.create_new_folder(path, sanitized_name)
                    
                    # Try selective refresh
                    if self.tree.refresh_directory_node(path):
                        # Restore all expanded paths
                        self.tree.restore_expanded_state(expanded_paths)
                        
                        # Ensure parent is expanded to show new folder
                        parent_item = self.tree.find_item_by_path(path)
                        if parent_item and not parent_item.isExpanded():
                            parent_item.setExpanded(True)
                        
                        # Select the new folder
                        new_item = self.tree.find_item_by_path(new_folder_path)
                        if new_item:
                            self.tree.setCurrentItem(new_item)
                            self.tree.scrollToItem(new_item)
                        elif current_selection:
                            # Restore previous selection if new item not found
                            selection_item = self.tree.find_item_by_path(current_selection)
                            if selection_item:
                                self.tree.setCurrentItem(selection_item)
                                scroll_bar.setValue(scroll_position)
                    else:
                        # Fallback to full refresh
                        self.load_tree(".")
                        self.tree.restore_expanded_state(expanded_paths)
                        new_item = self.tree.find_item_by_path(new_folder_path)
                        if new_item:
                            self.tree.setCurrentItem(new_item)
                            self.tree.scrollToItem(new_item)
                            
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create folder:\n{str(e)}")

    def create_new_md_file(self):
        # Determine selected directory
        selected_item = self.tree.currentItem()
        if selected_item:
            path = self.get_full_path(selected_item)
            if not os.path.isdir(path):
                path = os.path.dirname(path)
        else:
            path = "."

        filename, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and filename:
            if not filename.endswith(".md"):
                filename += ".md"
            new_file_path = os.path.join(path, filename)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Error", "File already exists.")
            else:
                try:
                    file_manager.create_new_file(path, filename)
                    # Use selective refresh instead of full reload
                    if not self.tree.refresh_directory_node(path):
                        self.load_tree(".")  # Fallback to full refresh
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create file:\n{str(e)}")

    def delete_selected(self):
        """Delete the currently selected file or folder"""
        selected_item = self.tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Error", "No item selected.")
            return

        path = self.get_full_path(selected_item)
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", "Selected item does not exist.")
            return

        # Check if it's a valid item to delete (.md file or directory)
        is_directory = os.path.isdir(path)
        is_md_file = os.path.isfile(path) and path.endswith(".md")
        
        if not is_directory and not is_md_file:
            QMessageBox.warning(self, "Error", "Only .md files and folders can be deleted.")
            return

        item_type = "folder" if is_directory else "file"
        
        # Show different confirmation messages for files vs folders
        if is_directory:
            # Count contents for folder deletion warning
            try:
                contents = os.listdir(path)
                file_count = len([f for f in contents if os.path.isfile(os.path.join(path, f))])
                folder_count = len([f for f in contents if os.path.isdir(os.path.join(path, f))])
                
                if contents:
                    content_msg = f"\nThis folder contains {file_count} file(s) and {folder_count} subfolder(s)."
                else:
                    content_msg = "\nThis folder is empty."
                    
                confirm_msg = f"Are you sure you want to delete the folder:\n{path}?{content_msg}\n\nThis action cannot be undone."
            except (PermissionError, OSError):
                confirm_msg = f"Are you sure you want to delete the folder:\n{path}?\n\nThis action cannot be undone."
        else:
            confirm_msg = f"Are you sure you want to delete the file:\n{path}?\n\nThis action cannot be undone."

        confirm = QMessageBox.question(
            self, f"Confirm Delete {item_type.title()}",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Store expanded state and current selection for restoration
                expanded_paths = self.tree.get_expanded_paths()
                parent_dir = os.path.dirname(path)
                
                # Clear current file if it's being deleted
                if self.current_file == path or (is_directory and self.current_file and self.current_file.startswith(path + os.sep)):
                    self.current_file = None
                    self.editor.clear()
                    self.render_html.setHtml("")
                    self.original_content = ""
                    self.has_unsaved_changes = False
                    self.update_save_button_style()
                    self.setWindowTitle("Markdown Manager - PyQt")
                
                # Remove the item from tree immediately to provide instant feedback
                parent_tree_item = selected_item.parent()
                if parent_tree_item:
                    parent_tree_item.removeChild(selected_item)
                else:
                    # Top level item
                    index = self.tree.indexOfTopLevelItem(selected_item)
                    if index >= 0:
                        self.tree.takeTopLevelItem(index)
                
                # Perform the actual deletion
                file_manager.delete_item(path)
                
                # Try selective refresh of parent directory
                refresh_success = False
                if os.path.isdir(parent_dir):
                    refresh_success = self.tree.refresh_directory_node(parent_dir)
                    
                    # Verify the refresh worked by checking if deleted item is still visible
                    if refresh_success:
                        deleted_item_check = self.tree.find_item_by_path(path)
                        if deleted_item_check is not None:
                            # Item is still visible, refresh failed
                            refresh_success = False
                            print(f"Selective refresh verification failed: deleted item still visible at {path}")
                
                if refresh_success:
                    # Restore expanded state after successful selective refresh
                    self.tree.restore_expanded_state(expanded_paths)
                    print(f"Selective refresh successful for {parent_dir}")
                else:
                    # Fallback to full tree reload
                    print(f"Selective refresh failed for {parent_dir}, performing full tree reload")
                    self.load_tree(".")
                    
                QMessageBox.information(self, "Success", f"{item_type.title()} deleted successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete {item_type}:\n{str(e)}")
                # On any error, do a full refresh to ensure tree is in correct state
                self.load_tree(".")

    # TREE
    def refresh_tree_preserve_state(self):
        """Refresh the entire tree while preserving expanded state and current selection"""
        try:
            # Store current state
            expanded_paths = self.tree.get_expanded_paths()
            current_selection_path = None
            
            if self.tree.currentItem():
                current_selection_path = self.get_full_path(self.tree.currentItem())
            
            # Temporarily disable the button and change text to show activity
            self.refresh_tree_btn.setText("Refreshing...")
            self.refresh_tree_btn.setEnabled(False)
            
            # Force update UI to show the button state change
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # Perform full tree reload
            self.load_tree(".")
            
            # Restore expanded state
            if expanded_paths:
                self.tree.restore_expanded_state(expanded_paths)
            
            # Restore selection if possible
            if current_selection_path:
                selection_item = self.tree.find_item_by_path(current_selection_path)
                if selection_item:
                    self.tree.setCurrentItem(selection_item)
                    self.tree.scrollToItem(selection_item)
            
            # Show brief success feedback
            self.refresh_tree_btn.setText("Refreshed!")
            
            # Use QTimer to reset button text after a short delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.reset_refresh_button())
            
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh tree:\n{str(e)}")
            self.reset_refresh_button()

    def load_tree(self, path):
        self.tree.clear()
        
        if platform.system() == "Windows":
            # On Windows, show all available drives
            drives = self.get_available_drives()
            current_abs_path = os.path.abspath(path)
            
            for drive in drives:
                # Create drive root item
                drive_item = QTreeWidgetItem([drive])
                drive_item.setData(0, Qt.UserRole, drive)
                self.tree.addTopLevelItem(drive_item)
                
                # If this drive contains our current path, expand it
                if current_abs_path.startswith(drive):
                    # Build path from drive to current directory
                    relative_path = os.path.relpath(current_abs_path, drive)
                    if relative_path != ".":
                        # Split path and create nested structure
                        path_parts = []
                        temp_path = relative_path
                        while temp_path and temp_path != ".":
                            path_parts.insert(0, os.path.basename(temp_path))
                            temp_path = os.path.dirname(temp_path)
                        
                        # Build nested structure
                        current_item = drive_item
                        current_path = drive
                        
                        for part in path_parts:
                            current_path = os.path.join(current_path, part)
                            
                            # Check if this child already exists
                            child_item = None
                            for i in range(current_item.childCount()):
                                child = current_item.child(i)
                                if child.text(0) == part:
                                    child_item = child
                                    break
                            
                            if not child_item:
                                child_item = QTreeWidgetItem([part])
                                child_item.setData(0, Qt.UserRole, current_path)
                                current_item.addChild(child_item)
                            
                            current_item = child_item
                        
                        # Add children to the final directory and expand
                        self.add_lazy_children(current_item, current_abs_path)
                        
                        # Expand the path to show current directory
                        item = drive_item
                        item.setExpanded(True)
                        while item.childCount() > 0:
                            item = item.child(0)  # Follow the path down
                            item.setExpanded(True)
                    else:
                        # Current path is at drive root
                        self.add_lazy_children(drive_item, drive)
                        drive_item.setExpanded(True)
                else:
                    # Add placeholder for lazy loading
                    try:
                        has_children = any(
                            os.path.isdir(os.path.join(drive, child)) or 
                            child.endswith(".md") 
                            for child in os.listdir(drive)
                        )
                        if has_children:
                            placeholder = QTreeWidgetItem(["Loading..."])
                            drive_item.addChild(placeholder)
                    except (PermissionError, OSError):
                        # If we can't read the drive, don't add placeholder
                        pass
        else:
            # Unix systems - use existing logic
            abs_path = os.path.abspath(path)
            path_parts = []
            
            # Build path components from root to current directory
            current = abs_path
            while current != os.path.dirname(current):  # Until we reach root
                path_parts.insert(0, current)
                current = os.path.dirname(current)
            path_parts.insert(0, current)  # Add root
            
            # Create tree structure showing full path
            parent_item = None
            for i, part in enumerate(path_parts):
                if i == 0:
                    # Root item
                    display_name = part if part != '/' else '/'
                    root_item = QTreeWidgetItem([display_name])
                    root_item.setData(0, Qt.UserRole, part)
                    self.tree.addTopLevelItem(root_item)
                    parent_item = root_item
                else:
                    # Child items
                    display_name = os.path.basename(part)
                    child_item = QTreeWidgetItem([display_name])
                    child_item.setData(0, Qt.UserRole, part)
                    parent_item.addChild(child_item)
                    parent_item = child_item
            
            # Add lazy loading placeholder and populate current directory
            if parent_item:
                self.add_lazy_children(parent_item, abs_path)
                parent_item.setExpanded(True)
        
        # Connect itemExpanded signal for lazy loading (if not already connected)
        try:
            self.tree.itemExpanded.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        self.tree.itemExpanded.connect(self.on_item_expanded)

    def add_lazy_children(self, parent_item, path):
        """Add children to a tree item with lazy loading support"""
        try:
            # Clear existing children (including any "Loading..." placeholders)
            parent_item.takeChildren()
            
            # Get directory contents
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path) or item_path.endswith(".md"):
                    items.append((item, item_path, os.path.isdir(item_path)))
            
            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x[2], x[0].lower()))
            
            for item_name, item_path, is_dir in items:
                # Add emoji prefix based on type
                if is_dir:
                    display_name = f"📁 {item_name}"
                else:
                    display_name = f"📄 {item_name}"
                    
                tree_item = QTreeWidgetItem([display_name])
                tree_item.setData(0, Qt.UserRole, item_path)  # Store full path
                parent_item.addChild(tree_item)
                
                # Add placeholder for directories to show expand arrow
                if is_dir:
                    # Check if directory has children
                    try:
                        has_children = any(
                            os.path.isdir(os.path.join(item_path, child)) or 
                            child.endswith(".md") 
                            for child in os.listdir(item_path)
                        )
                        if has_children:
                            placeholder = QTreeWidgetItem(["Loading..."])
                            tree_item.addChild(placeholder)
                    except (PermissionError, OSError):
                        # If we can't read the directory, don't add placeholder
                        pass
                        
        except (PermissionError, OSError) as e:
            # Handle permission errors gracefully
            error_item = QTreeWidgetItem([f"❌ Error: {str(e)}"])
            parent_item.addChild(error_item)

    def load_file_to_editor(self, item, column):
        try:
            path = self.get_full_path(item)
            
            # Validate the path exists and is accessible
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "Error", f"File not found: {path}")
                return
            
            if not os.path.isfile(path):
                # Not a file, ignore click
                return
                
            if not path.endswith(".md"):
                QMessageBox.warning(self, "Error", "Only .md files can be opened in the editor.")
                return
            
            # Attempt to load the file
            content = file_manager.load_file(path)
            self.editor.setPlainText(content)
            self.current_file = path
            self.original_content = content
            self.has_unsaved_changes = False
            self.update_save_button_style()
            self.update_rendered_view()
            
            # Update window title to show current file
            filename = os.path.basename(path)
            self.setWindowTitle(f"Markdown Manager - {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
            # Clear editor on error
            self.editor.clear()
            self.render_html.setHtml("")
            self.current_file = None
            self.original_content = ""
            self.has_unsaved_changes = False
            self.update_save_button_style()

    def on_item_expanded(self, item):
        """Handle lazy loading when an item is expanded"""
        item_path = item.data(0, Qt.UserRole)
        
        # Check if this item has a placeholder child or needs refresh
        if item.childCount() == 1:
            first_child = item.child(0)
            if first_child.text(0) == "Loading...":
                # Remove placeholder and load actual children
                item.removeChild(first_child)
                if os.path.isdir(item_path):
                    # Use the parent's add_lazy_children method
                    parent_widget = self.parent()
                    if hasattr(parent_widget, 'add_lazy_children'):
                        parent_widget.add_lazy_children(item, item_path)
                    else:
                        # Fallback direct implementation
                        try:
                            items = []
                            for child in os.listdir(item_path):
                                child_path = os.path.join(item_path, child)
                                if os.path.isdir(child_path) or child_path.endswith(".md"):
                                    items.append((child, child_path, os.path.isdir(child_path)))
                            
                            items.sort(key=lambda x: (not x[2], x[0].lower()))
                            
                            for child_name, child_path, is_dir in items:
                                if is_dir:
                                    display_name = f"📁 {child_name}"
                                else:
                                    display_name = f"📄 {child_name}"
                                    
                                tree_item = QTreeWidgetItem([display_name])
                                tree_item.setData(0, Qt.UserRole, child_path)
                                item.addChild(tree_item)
                                
                                if is_dir:
                                    try:
                                        has_children = any(
                                            os.path.isdir(os.path.join(child_path, grandchild)) or 
                                            grandchild.endswith(".md") 
                                            for grandchild in os.listdir(child_path)
                                        )
                                        if has_children:
                                            placeholder = QTreeWidgetItem(["Loading..."])
                                            tree_item.addChild(placeholder)
                                    except (PermissionError, OSError):
                                        pass
                        except (PermissionError, OSError):
                            error_item = QTreeWidgetItem(["❌ Access Denied"])
                            item.addChild(error_item)

    def get_full_path(self, item):
        """Get the full path stored in the item's data"""
        return item.data(0, Qt.UserRole) or ""

    def update_rendered_view(self):
        """Update the rendered HTML view with current content and styling"""
        md_text = self.editor.toPlainText()
        custom_css = self.style_editor.toPlainText()

        try:
            # Get the directory of the current file for relative path resolution
            base_dir = None
            if self.current_file:
                base_dir = os.path.dirname(os.path.abspath(self.current_file))
            else:
                base_dir = os.path.abspath(".")
            
            # Create temporary HTML file in the same directory as the markdown file
            temp_html_path = render.markdown_to_html(md_text, custom_css, save_temp_file=True, base_dir=base_dir)
            
            if temp_html_path and temp_html_path.endswith('.html'):
                # Load from file URL so relative paths work
                from PyQt5.QtCore import QUrl
                file_url = QUrl.fromLocalFile(os.path.abspath(temp_html_path))
                self.render_html.setUrl(file_url)
            else:
                # Fallback to setHtml if temp file creation failed
                self.render_html.setHtml(temp_html_path)
                
        except Exception as e:
            error_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #121212; color: #f0f0f0; padding: 20px;">
                <div style="background-color: #2c1e1e; border: 1px solid #e74c3c; padding: 20px; border-radius: 5px;">
                    <h3 style="color: #e74c3c; margin-top: 0;">Markdown Rendering Error</h3>
                    <p>Error rendering markdown: {str(e)}</p>
                    <p style="color: #bdc3c7; font-style: italic;">Please check your markdown syntax and try again.</p>
                </div>
            </body>
            </html>
            """
            self.render_html.setHtml(error_html)

    def handle_tab_change(self, index):
        """Handle tab changes and update preview when needed"""
        # Store previous tab index if it exists
        previous_tab = getattr(self, '_previous_tab_index', -1)
        
        # Update the preview in these cases:
        # 1. Switching to the Preview tab (index 1)
        # 2. Coming from the Style tab (index 2) to apply any CSS changes
        # 3. Coming from the Editor tab (index 0) to show content changes
        if index == 1 or previous_tab == 2 or previous_tab == 0:
            self.update_rendered_view()
        
        # Store the current tab index for next time
        self._previous_tab_index = index

    def get_available_drives(self):
        """Get all available drives on Windows, return current path on Unix"""
        if platform.system() == "Windows":
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
            return drives
        else:
            # On Unix systems, return root
            return ["/"]

    def run(self):
        self.show()

    def add_front_matter(self):
        if not self.current_file:
            QMessageBox.warning(self, "Error", "No file selected.")
            return
        
        current_content = self.editor.toPlainText()
        
        # Check if front matter already exists
        if current_content.strip().startswith("---"):
            reply = QMessageBox.question(
                self, "Front Matter Exists",
                "Front matter already exists. Replace it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            
            # Remove existing front matter
            lines = current_content.split('\n')
            if lines[0].strip() == "---":
                # Find the closing ---
                end_index = -1
                for i in range(1, len(lines)):
                    if lines[i].strip() == "---":
                        end_index = i
                        break
                
                if end_index > 0:
                    current_content = '\n'.join(lines[end_index + 1:]).lstrip('\n')
        
        # Add new front matter
        front_matter = self.config_manager.get_front_matter_template()
        new_content = front_matter + current_content
        
        self.editor.setPlainText(new_content)
        self.update_rendered_view()

    def reset_default_style(self):
        reply = QMessageBox.question(
            self, "Reset Style",
            "Are you sure you want to reset all styles to default?\nThis will overwrite your current style configuration.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                default_style = self.config_manager.get_default_style()
                self.style_editor.setPlainText(default_style)
                
                # Save the default style
                if self.config_manager.save_config(default_style):
                    QMessageBox.information(self, "Success", "Style reset to default successfully.")
                    self.update_rendered_view()
                else:
                    QMessageBox.warning(self, "Error", "Failed to save default style.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset style:\n{str(e)}")

    def save_style_config(self):
        """Save style configuration and update preview"""
        try:
            style_content = self.style_editor.toPlainText()
            if self.config_manager.save_config(style_content):
                # Force immediate preview update to show the changes
                self.update_rendered_view()
                QMessageBox.information(self, "Saved", "Style configuration saved successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to save style configuration.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save style:\n{str(e)}")

    def closeEvent(self, event):
        """Clean up temporary files on application close"""
        try:
            if self.current_file:
                base_dir = os.path.dirname(os.path.abspath(self.current_file))
                temp_file = os.path.join(base_dir, '.markdown_preview_temp.html')
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            # Also clean up in current directory
            temp_file = os.path.join(os.path.abspath("."), '.markdown_preview_temp.html')
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass  # Ignore cleanup errors
        
        event.accept()

class MarkdownTreeWidget(QTreeWidget):
    # Signal to inform parent to refresh the tree
    tree_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QTreeWidget.InternalMove)

    def startDrag(self, supportedActions):
        selected_item = self.currentItem()
        if not selected_item:
            return

        # Get the full path of the selected item
        path = self.get_full_path(selected_item)
        
        # Allow dragging both .md files and directories
        if not (os.path.isfile(path) and path.endswith(".md")) and not os.path.isdir(path):
            QMessageBox.warning(self, "Error", "Only .md files and folders can be dragged.")
            return

        # Create mime data with the file path
        mime_data = QMimeData()
        mime_data.setText(path)

        # Create and execute the drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        # Accept drag if it contains text (file path) and is a .md file or directory
        if event.mimeData().hasText():
            source_path = event.mimeData().text()
            if (os.path.isfile(source_path) and source_path.endswith(".md")) or os.path.isdir(source_path):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        # Same logic as dragEnterEvent
        if event.mimeData().hasText():
            source_path = event.mimeData().text()
            if (os.path.isfile(source_path) and source_path.endswith(".md")) or os.path.isdir(source_path):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def get_full_path(self, item):
        """Get the full path stored in the item's data"""
        return item.data(0, Qt.UserRole) or ""

    def get_expanded_paths(self):
        """Get all currently expanded paths"""
        expanded_paths = set()
        
        def collect_expanded(item):
            if item.isExpanded():
                path = self.get_full_path(item)
                if path:
                    expanded_paths.add(path)
            
            for i in range(item.childCount()):
                collect_expanded(item.child(i))
        
        for i in range(self.topLevelItemCount()):
            collect_expanded(self.topLevelItem(i))
        
        return expanded_paths

    def restore_expanded_state(self, expanded_paths):
        """Restore expanded state for given paths"""
        if not expanded_paths:
            return
        
        def expand_items(item):
            path = self.get_full_path(item)
            if path and path in expanded_paths:
                # First ensure all children are loaded if this is a lazy-loaded item
                if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
                    # Trigger lazy loading by simulating expansion
                    item.removeChild(item.child(0))
                    parent_widget = self.parent()
                    if hasattr(parent_widget, 'add_lazy_children'):
                        parent_widget.add_lazy_children(item, path)
                
                # Now expand the item
                item.setExpanded(True)
            
            # Process all children
            for i in range(item.childCount()):
                child = item.child(i)
                if child.text(0) != "Loading...":  # Skip placeholder items
                    expand_items(child)
        
        # Process all top-level items
        for i in range(self.topLevelItemCount()):
            expand_items(self.topLevelItem(i))
        
        # Force a visual update
        self.update()

    def find_item_by_path(self, target_path):
        """Find tree item by its full path with improved reliability"""
        if not target_path:
            return None
        
        # Normalize the target path
        target_path = os.path.normpath(target_path)
        
        def search_item(item):
            item_path = self.get_full_path(item)
            if item_path:
                # Normalize the item path for comparison
                normalized_item_path = os.path.normpath(item_path)
                if normalized_item_path == target_path:
                    return item
            
            # Search children
            for i in range(item.childCount()):
                result = search_item(item.child(i))
                if result:
                    return result
            return None
        
        # Search all top-level items
        for i in range(self.topLevelItemCount()):
            result = search_item(self.topLevelItem(i))
            if result:
                return result
        return None

    def refresh_directory_node(self, dir_path):
        """Refresh only a specific directory node while preserving state"""
        if not os.path.isdir(dir_path):
            return False
        
        # Find the item representing this directory
        dir_item = self.find_item_by_path(dir_path)
        if not dir_item:
            return False
        
        try:
            # Store expanded state of all children before refresh
            children_expanded_state = {}
            for i in range(dir_item.childCount()):
                child = dir_item.child(i)
                child_path = self.get_full_path(child)
                if child_path:
                    children_expanded_state[child_path] = child.isExpanded()
            
            # Store the main directory's expanded state
            was_expanded = dir_item.isExpanded()
            
            # Clear all children first to remove any "Loading..." placeholders
            dir_item.takeChildren()
            
            # Get current directory contents from filesystem
            items = []
            try:
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if os.path.isdir(item_path) or item_path.endswith(".md"):
                        items.append((item, item_path, os.path.isdir(item_path)))
            except (PermissionError, OSError) as e:
                # Handle permission errors gracefully
                error_item = QTreeWidgetItem([f"❌ Error: Access Denied"])
                dir_item.addChild(error_item)
                return False
            
            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x[2], x[0].lower()))
            
            # Create new tree items with proper icons
            for item_name, item_path, is_dir in items:
                # Add emoji prefix based on type
                if is_dir:
                    display_name = f"📁 {item_name}"
                else:
                    display_name = f"📄 {item_name}"
                    
                tree_item = QTreeWidgetItem([display_name])
                tree_item.setData(0, Qt.UserRole, item_path)
                dir_item.addChild(tree_item)
                
                # Add placeholder for directories to show expand arrow
                if is_dir:
                    try:
                        has_children = any(
                            os.path.isdir(os.path.join(item_path, child)) or 
                            child.endswith(".md") 
                            for child in os.listdir(item_path)
                        )
                        if has_children:
                            placeholder = QTreeWidgetItem(["Loading..."])
                            tree_item.addChild(placeholder)
                    except (PermissionError, OSError):
                        # If we can't read the directory, don't add placeholder
                        pass
                
                # Restore expanded state for this child
                if item_path in children_expanded_state and children_expanded_state[item_path]:
                    tree_item.setExpanded(True)
                    # If this child was expanded, we need to load its children too
                    if is_dir:
                        self.add_lazy_children(tree_item, item_path)
            
            # Restore main directory expanded state
            if was_expanded:
                dir_item.setExpanded(True)
            
            return True
            
        except Exception as e:
            print(f"Error refreshing directory {dir_path}: {str(e)}")
            return False

    def refresh_after_move(self, expanded_paths, moved_from_path, moved_to_path, selected_path=None):
        """Refresh tree after a move operation, preserving state"""
        # Find the main application window
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'load_tree'):
            main_window = main_window.parent()
        
        if main_window and hasattr(main_window, 'load_tree'):
            # Reload the tree completely
            main_window.load_tree(".")
            
            # Restore expanded state
            if expanded_paths:
                self.restore_expanded_state(expanded_paths)
            
            # Handle selection
            if selected_path == moved_from_path:
                # Select the moved item in its new location
                moved_item = self.find_item_by_path(moved_to_path)
                if moved_item:
                    self.setCurrentItem(moved_item)
                    self.scrollToItem(moved_item)
            elif selected_path:
                # Try to restore original selection
                selection_item = self.find_item_by_path(selected_path)
                if selection_item:
                    self.setCurrentItem(selection_item)
                    self.scrollToItem(selection_item)
            
            # Force update
            self.update()
            return True
        
        return False

    def dropEvent(self, event):
        try:
            source_path = event.mimeData().text()
            
            # Validate source is either .md file or directory
            if not ((os.path.isfile(source_path) and source_path.endswith(".md")) or os.path.isdir(source_path)):
                QMessageBox.warning(self, "Error", "Only .md files and folders can be moved.")
                event.ignore()
                return

            # Get the target item where the file/folder is being dropped
            target_item = self.itemAt(event.pos())
            if not target_item:
                event.ignore()
                return

            # Get the full path of the target
            target_path = self.get_full_path(target_item)
            
            # If target is a file, use its parent directory
            if os.path.isfile(target_path):
                target_path = os.path.dirname(target_path)
            
            # Validate target is a directory
            if not os.path.isdir(target_path):
                QMessageBox.warning(self, "Error", "Invalid drop target.")
                event.ignore()
                return

            # Special validation for folder moves: prevent moving into own subfolder
            if os.path.isdir(source_path):
                # Normalize paths for comparison
                norm_source = os.path.normpath(source_path)
                norm_target = os.path.normpath(target_path)
                
                # Check if target is within source (would create infinite loop)
                if norm_target.startswith(norm_source + os.sep) or norm_target == norm_source:
                    QMessageBox.warning(self, "Error", "Cannot move a folder into itself or its subfolder.")
                    event.ignore()
                    return

            # Get source directory for refresh purposes
            source_dir = os.path.dirname(source_path)

            # Create the new path
            new_path = os.path.join(target_path, os.path.basename(source_path))

            # Check if source and target are the same
            if source_path == new_path:
                event.ignore()
                return

            # Check if item already exists in target location
            if os.path.exists(new_path):
                item_type = "folder" if os.path.isdir(source_path) else "file"
                QMessageBox.warning(self, "Error", f"A {item_type} with this name already exists in the target folder.")
                event.ignore()
                return

            # Store current tree state BEFORE the move operation
            expanded_paths = self.get_expanded_paths()
            current_selection_path = self.get_full_path(self.currentItem()) if self.currentItem() else None

            # Determine if we need to use cross-drive operations
            try:
                from utils import confirm_move_operation
                import file_manager
                
                # Check if this is a cross-drive operation
                is_cross_drive = file_manager.check_cross_drive_operation(source_path, new_path)
                
                if is_cross_drive:
                    # For cross-drive operations, show confirmation dialog
                    proceed, verify_integrity = confirm_move_operation(source_path, new_path, self)
                    if not proceed:
                        event.ignore()
                        return
            except ImportError:
                # Fallback if utils not available
                is_cross_drive = False

            # Perform the move operation
            try:
                if is_cross_drive:
                    # Use shutil.move for cross-drive operations
                    import shutil
                    shutil.move(source_path, new_path)
                else:
                    # Use efficient rename for same-drive operations
                    os.rename(source_path, new_path)
                    
            except (OSError, IOError) as e:
                QMessageBox.critical(self, "Move Error", f"Failed to move item:\n{str(e)}")
                event.ignore()
                return
            
            # Find the main application window (MarkdownManagerApp)
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'load_tree'):
                main_window = main_window.parent()
            
            # Update current file reference if it was moved
            if main_window and hasattr(main_window, 'current_file') and main_window.current_file:
                if main_window.current_file == source_path:
                    main_window.current_file = new_path
                elif os.path.isdir(source_path) and main_window.current_file.startswith(source_path + os.sep):
                    # Update file path if it was inside a moved directory
                    relative_path = os.path.relpath(main_window.current_file, source_path)
                    main_window.current_file = os.path.join(new_path, relative_path)
            
            # Perform tree refresh - use the exact same approach as the refresh button
            if main_window and hasattr(main_window, 'load_tree'):
                try:
                    # Clear and reload the entire tree (same as refresh button)
                    main_window.load_tree(".")
                    
                    # Restore expanded state
                    if expanded_paths:
                        self.restore_expanded_state(expanded_paths)
                    
                    # Handle selection restoration
                    selection_restored = False
                    
                    # If the moved item was originally selected, select it in new location
                    if current_selection_path == source_path:
                        moved_item = self.find_item_by_path(new_path)
                        if moved_item:
                            self.setCurrentItem(moved_item)
                            self.scrollToItem(moved_item)
                            selection_restored = True
                    elif current_selection_path and os.path.isdir(source_path) and current_selection_path.startswith(source_path + os.sep):
                        # If selected item was inside moved directory, update its path
                        relative_path = os.path.relpath(current_selection_path, source_path)
                        new_selection_path = os.path.join(new_path, relative_path)
                        moved_item = self.find_item_by_path(new_selection_path)
                        if moved_item:
                            self.setCurrentItem(moved_item)
                            self.scrollToItem(moved_item)
                            selection_restored = True
                    
                    # If we couldn't restore selection to moved item, try original selection
                    if not selection_restored and current_selection_path:
                        selection_item = self.find_item_by_path(current_selection_path)
                        if selection_item:
                            self.setCurrentItem(selection_item)
                            self.scrollToItem(selection_item)
                    
                    # Force UI update
                    self.update()
                    if main_window:
                        main_window.update()
                    
                    print(f"Tree refreshed after moving {source_path} to {new_path}")
                    
                except Exception as refresh_error:
                    print(f"Tree refresh failed: {refresh_error}")
                    # If automatic refresh fails, highlight the refresh button
                    if hasattr(main_window, 'refresh_tree_btn'):
                        main_window.refresh_tree_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #ff8c00;
                                color: #f0f0f0;
                                border: 1px solid #333;
                                padding: 8px 12px;
                                border-radius: 3px;
                                font-weight: bold;
                            }
                        """)
                        main_window.refresh_tree_btn.setText("Refresh Needed")
            else:
                print("Could not find main window for tree refresh")
            
            event.acceptProposedAction()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to move item:\n{str(e)}")
            event.ignore()
