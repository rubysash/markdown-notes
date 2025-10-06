# gui.py

import os
import platform
import sys
import time
from PyQt5.QtWidgets import (
    QMainWindow, QTreeWidget, QTreeWidgetItem, QSplitter, QWidget,
    QVBoxLayout, QPlainTextEdit, QMessageBox, QTabWidget, QPushButton, 
    QInputDialog, QShortcut, QMenu, QHBoxLayout, QLineEdit, QCheckBox,
    QLabel, QStyle
)

from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, QMimeData, QByteArray, QSize
from PyQt5.QtGui import (QFont, QKeySequence, QDrag, QTextDocument,
                         QTextCursor, QIcon, QPixmap, QPainter)
from PyQt5.QtSvg import QSvgRenderer

from PyQt5.QtPrintSupport import QPrintDialog, QPrinter

from clipboard_handler import ClipboardImageHandler
from assets import (SVG_ICON_CASE, SVG_ICON_SEARCH, SVG_ICON_CLEAR,
                    ICON_BUTTON_STYLE)
import file_manager
import render

def create_icon_from_svg(svg_data: str) -> QIcon:
    """Creates a QIcon from raw SVG data."""
    try:
        svg_bytes = QByteArray(svg_data.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(renderer.defaultSize())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except Exception as e:
        print(f"Error creating SVG icon: {e}")
        return QIcon()

class SearchWorker(QObject):
    """
    Worker thread for performing file search without freezing the GUI.
    """
    # Signal with a list of matching file paths
    results_ready = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, root_path, search_term, case_sensitive=False):
        super().__init__()
        self.root_path = root_path
        # Store the search term, lowercasing it only if the search is insensitive.
        self.search_term = search_term if case_sensitive else search_term.lower()
        self.case_sensitive = case_sensitive
        self.is_running = True

    def run(self):
        """
        Walks the directory tree and searches file names and contents.
        """
        matching_files = set()
        try:
            for root, _, files in os.walk(self.root_path):
                if not self.is_running:
                    break
                for filename in files:
                    if not self.is_running:
                        break
                    
                    file_path = os.path.join(root, filename)
                    
                    # Prepare filename for comparison based on case sensitivity.
                    search_in_filename = filename if self.case_sensitive else filename.lower()
                    if self.search_term in search_in_filename:
                        matching_files.add(file_path)
                        continue  # Already matched, no need to check content

                    # Search in content for .md files
                    if filename.endswith(".md"):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                # Prepare content for comparison based on case sensitivity.
                                search_in_content = content if self.case_sensitive else content.lower()
                                if self.search_term in search_in_content:
                                    matching_files.add(file_path)
                        except (IOError, OSError):
                            # Ignore files we can't read
                            continue
        except Exception as e:
            print(f"Error during search: {e}")
        finally:
            if self.is_running:
                self.results_ready.emit(sorted(list(matching_files)))
            self.finished.emit()

    def stop(self):
        self.is_running = False

class SearchWidget(QWidget):
    """A widget for text search functionality."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
        self.hide()

    def setupUi(self):
        """Initializes the UI components of the search widget."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")
        layout.addWidget(self.search_input)

        self.prev_btn = QPushButton("Previous")
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next")
        layout.addWidget(self.next_btn)

        self.case_checkbox = QCheckBox("Match Case")
        layout.addWidget(self.case_checkbox)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class MarkdownManagerApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Manager")

        # Initialize config manager
        from config import ConfigManager
        self.config_manager = ConfigManager()

        # Initialize clipboard handler
        self.clipboard_handler = ClipboardImageHandler()

        # Track unsaved changes and filter state
        self.has_unsaved_changes = False
        self.is_filtered = False
        self.search_thread = None
        self.search_worker = None
        self.root_path = "."  # Default root path

        # Create menu bar
        self._create_menu_bar()

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Left panel layout
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Setup the new filter widget with buttons
        self._setup_filter_widget(left_layout)

        self.save_button = QPushButton()
        self.save_button.clicked.connect(self.save_current_file)
        left_layout.addWidget(self.save_button)

        self.tree = MarkdownTreeWidget(self)
        self.tree.setHeaderHidden(True)
        left_layout.addWidget(self.tree)

        # Connect the custom signal to refresh tree
        self.tree.tree_updated.connect(lambda: self.load_tree(self.root_path))

        # Add context menu to tree
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Keybinds for actions not in the main menu
        rename_shortcut = QShortcut(QKeySequence(Qt.Key_F2), self)
        rename_shortcut.activated.connect(self.handle_rename_shortcut)

        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.toggle_search_widget)

        splitter.addWidget(left_panel)
        
        # Determine and set up the default directory
        try:
            # Get the directory where the application script is located
            script_dir = os.path.dirname(
                os.path.abspath(sys.modules['__main__'].__file__)
            )
            self.project_root = script_dir 
            docs_path = os.path.join(script_dir, "docs")
            
            # Create the 'docs' directory if it doesn't exist
            os.makedirs(docs_path, exist_ok=True)
            self.root_path = docs_path

        except Exception as e:
            # Fallback to current working directory if path detection fails
            print(f"Error setting up default directory: {e}")
            self.project_root = os.getcwd() 
            self.root_path = "."
        
        self.load_tree(self.root_path)

        # Right panel - Tab widget and Search
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_panel.setLayout(right_layout)

        self.tab_widget = QTabWidget()
        right_layout.addWidget(self.tab_widget)
        
        self.search_widget = SearchWidget(self)
        right_layout.addWidget(self.search_widget)
        
        splitter.addWidget(right_panel)

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
        
        config_content = self.config_manager.load_config()
        self.style_editor.setPlainText(config_content)
        
        self.tab_widget.addTab(self.style_editor, "Style")

        self.current_file = None
        self.original_content = ""

        self.tree.itemClicked.connect(self.load_file_to_editor)
        self.editor.textChanged.connect(self.on_editor_text_changed)
        self.style_editor.textChanged.connect(self.update_rendered_view)
        self.tab_widget.currentChanged.connect(self.handle_tab_change)

        # Connect search signals
        self.search_widget.next_btn.clicked.connect(self.find_next)
        self.search_widget.prev_btn.clicked.connect(self.find_previous)
        self.search_widget.search_input.returnPressed.connect(self.find_next)
        self.search_widget.search_input.textChanged.connect(
            self.handle_search_text_changed
        )

        splitter.setSizes([250, 750])
        
        splitter.setChildrenCollapsible(True)
        left_panel.setMinimumSize(150, 0)
        right_panel.setMinimumSize(300, 0)

        self.update_save_button_style()

    def _setup_filter_widget(self, parent_layout):
        """Creates and configures the file filter input and buttons."""
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter files and content...")
        self.filter_input.returnPressed.connect(self._start_search)
        filter_layout.addWidget(self.filter_input)

        # Case sensitive search button
        self.case_sensitive_button = QPushButton()
        self.case_sensitive_button.setIcon(create_icon_from_svg(SVG_ICON_CASE))
        self.case_sensitive_button.setIconSize(QSize(20, 20))
        self.case_sensitive_button.setCheckable(True)
        self.case_sensitive_button.setFixedSize(28, 28)
        self.case_sensitive_button.setToolTip("Match Case")
        self.case_sensitive_button.setStyleSheet(ICON_BUTTON_STYLE)
        filter_layout.addWidget(self.case_sensitive_button)

        # Find button
        self.find_button = QPushButton()
        self.find_button.setIcon(create_icon_from_svg(SVG_ICON_SEARCH))
        self.find_button.setIconSize(QSize(20, 20))
        self.find_button.setFixedSize(28, 28)
        self.find_button.setToolTip("Find")
        self.find_button.clicked.connect(self._start_search)
        self.find_button.setStyleSheet(ICON_BUTTON_STYLE)
        filter_layout.addWidget(self.find_button)

        # Clear button
        self.clear_button = QPushButton()
        self.clear_button.setIcon(create_icon_from_svg(SVG_ICON_CLEAR))
        self.clear_button.setIconSize(QSize(20, 20))
        self.clear_button.setFixedSize(28, 28)
        self.clear_button.setToolTip("Clear filter and show all files")
        self.clear_button.clicked.connect(self._clear_filter)
        self.clear_button.setStyleSheet(ICON_BUTTON_STYLE)
        filter_layout.addWidget(self.clear_button)
        
        parent_layout.addLayout(filter_layout)

    def _start_search(self):
        """Initiates the file search in a background thread."""
        search_term = self.filter_input.text()  # Removed .strip()
        if not search_term:
            self._clear_filter()
            return

        # Stop previous search if it's still running
        if self.search_thread and self.search_thread.isRunning():
            self.search_worker.stop()
            self.search_thread.quit()
            self.search_thread.wait()

        self.filter_input.setEnabled(False)
        self.find_button.setEnabled(False)
        self.case_sensitive_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.tree.clear()
        loading_item = QTreeWidgetItem(["Searching..."])
        self.tree.addTopLevelItem(loading_item)

        # Check case sensitivity state
        is_case_sensitive = self.case_sensitive_button.isChecked()

        # Setup and start the new search thread
        self.search_thread = QThread()
        self.search_worker = SearchWorker(
            self.root_path, search_term, case_sensitive=is_case_sensitive
        )
        self.search_worker.moveToThread(self.search_thread)

        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.results_ready.connect(self._update_tree_with_filter)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self._on_search_complete)

        self.search_thread.start()

    def _update_tree_with_filter(self, matching_files):
        """Rebuilds the tree view to show only the search results."""
        self.tree.clear()
        self.is_filtered = True
        
        if not matching_files:
            no_results_item = QTreeWidgetItem(["No matches found."])
            self.tree.addTopLevelItem(no_results_item)
            return

        # A dictionary to keep track of created tree items by their path
        nodes = {}
        root_path_abs = os.path.abspath(self.root_path)

        for path in matching_files:
            # Make path relative to the root for tree building
            relative_path = os.path.relpath(path, os.path.dirname(root_path_abs))
            
            # Split path into parts (docs, folder, file.md)
            path_parts = relative_path.split(os.sep)
            
            parent_item = None
            current_path_so_far = os.path.dirname(root_path_abs)

            for i, part in enumerate(path_parts):
                current_path_so_far = os.path.join(current_path_so_far, part)
                
                if current_path_so_far in nodes:
                    parent_item = nodes[current_path_so_far]
                    continue

                # Create new item
                is_dir = (i < len(path_parts) - 1) or os.path.isdir(path)
                display_name = f"📁 {part}" if is_dir else f"📄 {part}"
                new_item = QTreeWidgetItem([display_name])
                new_item.setData(0, Qt.UserRole, current_path_so_far)
                nodes[current_path_so_far] = new_item
                
                if parent_item:
                    parent_item.addChild(new_item)
                else:
                    self.tree.addTopLevelItem(new_item)
                
                parent_item = new_item
        
        # Expand all items in the filtered view for clarity
        self.tree.expandAll()

    def _clear_filter(self):
        """Resets the filter and reloads the full directory tree."""
        if self.search_thread and self.search_thread.isRunning():
            self.search_worker.stop()
            self.search_thread.quit()
            self.search_thread.wait()

        self.filter_input.clear()
        self.is_filtered = False
        self.load_tree(self.root_path)

    def _on_search_complete(self):
        """Re-enables UI elements after a search is complete."""
        self.filter_input.setEnabled(True)
        self.find_button.setEnabled(True)
        self.case_sensitive_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    # Events
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
        self.update_window_title()
        self.update_rendered_view()
        self.update_save_button_style()

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
                print_css = self.config_manager.load_print_css()
                import render
                
                # Pass project_root to the renderer
                html_content = render.markdown_to_html_for_browser_print(md_text, print_css, self.current_file, project_root=self.project_root)
                
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
            if not self.current_file:
                QMessageBox.warning(self, "No File Open", "Please open a markdown file before pasting an image.")
                return
            
            if not self.clipboard_handler.has_image_in_clipboard():
                QMessageBox.information(self, "No Image", "No image found in clipboard.")
                return
            
            self.clipboard_handler.ensure_images_folder()
            result = self.clipboard_handler.process_clipboard_image()
            
            if result:
                relative_path_from_root, absolute_path = result
                
                alt_text, ok = QInputDialog.getText(self, "Image Description", "Enter alt text for the image (optional):", text="Pasted Image")
                if not ok:
                    alt_text = "Pasted Image"
                
                # Create a clean, root-relative path for portability (e.g., for Hugo)
                markdown_image_path = f"/{relative_path_from_root.replace(os.sep, '/')}"

                markdown_link = self.clipboard_handler.create_markdown_image_link(alt_text, markdown_image_path)
                
                cursor = self.editor.textCursor()
                
                if not cursor.atBlockStart():
                    markdown_link = '\n' + markdown_link
                if not cursor.atBlockEnd():
                    markdown_link = markdown_link + '\n'
                
                cursor.insertText(markdown_link)
                self.update_rendered_view()
                
                QMessageBox.information(self, "Image Pasted", f"Image saved to: {relative_path_from_root}")
            else:
                QMessageBox.critical(self, "Paste Failed", "Failed to save the image from clipboard.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while pasting the image:\n{str(e)}")

    # Search Widget
    def toggle_search_widget(self):
        """Shows or hides the search widget and focuses the input field."""
        if self.search_widget.isVisible():
            self.search_widget.hide()
        else:
            self.search_widget.show()
            self.search_widget.search_input.setFocus()
            self.search_widget.search_input.selectAll()

    def _get_search_flags(self):
        """Gets search flags based on UI controls for editor and web view."""
        editor_flags = QTextDocument.FindFlags()
        web_flags = QWebEnginePage.FindFlags()

        if self.search_widget.case_checkbox.isChecked():
            editor_flags |= QTextDocument.FindCaseSensitively
            web_flags |= QWebEnginePage.FindCaseSensitively
        
        return editor_flags, web_flags

    def find_next(self):
        """Finds the next occurrence of the search text."""
        self._find_text(find_next=True)

    def find_previous(self):
        """Finds the previous occurrence of the search text."""
        self._find_text(find_next=False)

    def _find_text(self, find_next=True):
        """
        Core search logic for both editor and preview tabs.
        It wraps around the document when the end or beginning is reached.
        """
        search_text = self.search_widget.search_input.text()
        if not search_text:
            return

        current_tab_index = self.tab_widget.currentIndex()
        editor_flags, web_flags = self._get_search_flags()

        if not find_next:
            editor_flags |= QTextDocument.FindBackward
            web_flags |= QWebEnginePage.FindBackward

        # Search in Editor (Tab 0)
        if current_tab_index == 0:
            found = self.editor.find(search_text, editor_flags)
            if not found:
                # Wrap search
                cursor = self.editor.textCursor()
                if find_next:
                    cursor.movePosition(QTextCursor.Start)
                else:
                    cursor.movePosition(QTextCursor.End)
                self.editor.setTextCursor(cursor)
                self.editor.find(search_text, editor_flags)
        
        # Search in Preview (Tab 1)
        elif current_tab_index == 1:
            self.render_html.findText(search_text, web_flags)
        
        # Other tabs (like Style) are not searchable with this feature.

    def handle_search_text_changed(self, text):
        """Clears search highlights if the search text is empty."""
        if not text:
            current_tab_index = self.tab_widget.currentIndex()
            if current_tab_index == 0:
                # Clear selection in editor
                cursor = self.editor.textCursor()
                cursor.clearSelection()
                self.editor.setTextCursor(cursor)
            elif current_tab_index == 1:
                # Clear highlights in preview
                self.render_html.findText("")

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
                    # Store state before any operations
                    expanded_paths = self.tree.get_expanded_paths()
                    current_selection = None
                    if self.tree.currentItem():
                        current_selection = self.get_full_path(self.tree.currentItem())
                    
                    # Create the folder
                    file_manager.create_new_folder(target_path, sanitized_name)
                    
                    # Always use selective refresh for folder creation
                    refresh_success = self.tree.refresh_directory_node(target_path)
                    
                    if refresh_success:
                        # Ensure parent is expanded to show new folder
                        parent_item = self.tree.find_item_by_path(target_path)
                        if parent_item and not parent_item.isExpanded():
                            parent_item.setExpanded(True)
                        
                        # Select the newly created folder
                        from PyQt5.QtCore import QTimer
                        def select_new_folder():
                            new_item = self.tree.find_item_by_path(new_folder_path)
                            if new_item:
                                self.tree.setCurrentItem(new_item)
                                self.tree.scrollToItem(new_item)
                        
                        # Use timer to ensure tree is fully updated before selection
                        QTimer.singleShot(100, select_new_folder)
                        
                    else:
                        print("Selective refresh failed, falling back to full refresh")
                        # Full refresh fallback
                        self.load_tree(".")
                        self.tree.restore_expanded_state(expanded_paths)
                        
                        # Try to select new folder after full refresh
                        from PyQt5.QtCore import QTimer
                        def select_after_full_refresh():
                            new_item = self.tree.find_item_by_path(new_folder_path)
                            if new_item:
                                self.tree.setCurrentItem(new_item)
                                self.tree.scrollToItem(new_item)
                        
                        QTimer.singleShot(200, select_after_full_refresh)
                            
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
                self.editor.setReadOnly(False)
                content = file_manager.load_file(file_path)
                self.editor.setPlainText(content)
                self.current_file = file_path
                self.original_content = content
                self.has_unsaved_changes = False
                self.update_window_title()
                self.update_rendered_view()
                
                # Select the file in the tree
                file_item = self.tree.find_item_by_path(file_path)
                if file_item:
                    self.tree.setCurrentItem(file_item)
                    self.tree.scrollToItem(file_item)
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to load file:\n{str(e)}"
                )

    # CRUD
    def save_current_file(self):
        """Save the current file or style configuration"""
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
            self.update_window_title()
            # This line tells the button to update after a successful save
            self.update_save_button_style()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save file:\n{str(e)}"
            )

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

        is_directory = os.path.isdir(path)
        is_md_file = os.path.isfile(path) and path.endswith(".md")
        
        if not is_directory and not is_md_file:
            QMessageBox.warning(
                self, "Error", "Only .md files and folders can be deleted."
            )
            return

        item_type = "folder" if is_directory else "file"
        
        if is_directory:
            try:
                contents = os.listdir(path)
                file_count = len(
                    [f for f in contents 
                     if os.path.isfile(os.path.join(path, f))]
                )
                folder_count = len(
                    [f for f in contents 
                     if os.path.isdir(os.path.join(path, f))]
                )
                
                content_msg = (
                    f"\nThis folder contains {file_count} file(s) and "
                    f"{folder_count} subfolder(s)."
                ) if contents else "\nThis folder is empty."
                    
                confirm_msg = (
                    f"Are you sure you want to delete the folder:\n{path}?"
                    f"{content_msg}\n\nThis action cannot be undone."
                )
            except (PermissionError, OSError):
                confirm_msg = (
                    f"Are you sure you want to delete the folder:\n{path}?"
                    f"\n\nThis action cannot be undone."
                )
        else:
            confirm_msg = (
                f"Are you sure you want to delete the file:\n{path}?"
                f"\n\nThis action cannot be undone."
            )

        confirm = QMessageBox.question(
            self, f"Confirm Delete {item_type.title()}",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                expanded_paths = self.tree.get_expanded_paths()
                parent_dir = os.path.dirname(path)
                
                if self.current_file == path or (
                    is_directory and self.current_file and 
                    self.current_file.startswith(path + os.sep)
                ):
                    self.current_file = None
                    self.editor.clear()
                    self.render_html.setHtml("")
                    self.original_content = ""
                    self.has_unsaved_changes = False
                    self.update_window_title()
                
                parent_tree_item = selected_item.parent()
                if parent_tree_item:
                    parent_tree_item.removeChild(selected_item)
                else:
                    index = self.tree.indexOfTopLevelItem(selected_item)
                    if index >= 0:
                        self.tree.takeTopLevelItem(index)
                
                file_manager.delete_item(path)
                
                refresh_success = False
                if os.path.isdir(parent_dir):
                    refresh_success = self.tree.refresh_directory_node(
                        parent_dir
                    )
                    
                    if refresh_success:
                        deleted_item_check = self.tree.find_item_by_path(path)
                        if deleted_item_check is not None:
                            refresh_success = False
                
                if refresh_success:
                    self.tree.restore_expanded_state(expanded_paths)
                else:
                    self.load_tree(".")
                    
                QMessageBox.information(
                    self, "Success", f"{item_type.title()} deleted successfully."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to delete {item_type}:\n{str(e)}"
                )
                self.load_tree(".")

    # TREE
    def refresh_tree_preserve_state(self):
        """Refresh tree while preserving expanded state and selection."""
        try:
            expanded_paths = set()
            
            def collect_expanded(item):
                path = self.get_full_path(item)
                if path and item.isExpanded():
                    expanded_paths.add(path)
                for i in range(item.childCount()):
                    collect_expanded(item.child(i))
            
            for i in range(self.tree.topLevelItemCount()):
                collect_expanded(self.tree.topLevelItem(i))
            
            current_selection_path = None
            if self.tree.currentItem():
                current_selection_path = self.get_full_path(
                    self.tree.currentItem()
                )
            
            scroll_bar = self.tree.verticalScrollBar()
            scroll_position = scroll_bar.value()
            
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            self.load_tree(".")
            
            QCoreApplication.processEvents()
            
            for path in expanded_paths:
                if os.path.exists(path):
                    item = self.tree.find_item_by_path(path)
                    if item:
                        parent = item.parent()
                        parent_stack = []
                        while parent:
                            parent_stack.append(parent)
                            parent = parent.parent()
                        
                        while parent_stack:
                            parent = parent_stack.pop()
                            if not parent.isExpanded():
                                parent.setExpanded(True)
                                self.on_item_expanded(parent)
                        
                        if not item.isExpanded():
                            item.setExpanded(True)
                            self.on_item_expanded(item)
            
            if current_selection_path and os.path.exists(
                current_selection_path
            ):
                selection_item = self.tree.find_item_by_path(
                    current_selection_path
                )
                if selection_item:
                    self.tree.setCurrentItem(selection_item)
                    self.tree.scrollToItem(selection_item)
                else:
                    scroll_bar.setValue(scroll_position)
            
        except Exception as e:
            QMessageBox.warning(
                self, "Refresh Error", f"Failed to refresh tree:\n{str(e)}"
            )

    # Load Just the docs
    def load_tree(self, path):
        """Loads the directory structure from the given path into the tree."""
        self.tree.clear()
        
        try:
            root_path = os.path.abspath(path)
            if not os.path.isdir(root_path):
                QMessageBox.critical(
                    self, "Error", f"Base path is not a directory: {root_path}"
                )
                return

            # Use the directory name as the root item in the tree
            root_display_name = f"📁 {os.path.basename(root_path)}"
            root_item = QTreeWidgetItem([root_display_name])
            root_item.setData(0, Qt.UserRole, root_path)
            self.tree.addTopLevelItem(root_item)
            
            # Populate the root item with its contents and expand it
            self.add_lazy_children(root_item, root_path)
            root_item.setExpanded(True)

        except Exception as e:
            QMessageBox.critical(
                self, "Error Loading Tree", f"Failed to load file tree: {e}"
            )

        # Connect itemExpanded signal for lazy loading
        try:
            self.tree.itemExpanded.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        self.tree.itemExpanded.connect(self.on_item_expanded)

    # Load Full drive
    def UNUSED_load_tree(self, path):
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
            
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "Error", f"File not found: {path}")
                return
            
            if not os.path.isfile(path):
                return
                
            if not path.endswith(".md"):
                QMessageBox.warning(
                    self, "Error", 
                    "Only .md files can be opened in the editor."
                )
                return
            
            self.editor.setReadOnly(False)
            content = file_manager.load_file(path)
            self.editor.setPlainText(content)
            self.current_file = path
            self.original_content = content
            self.has_unsaved_changes = False
            self.update_window_title()
            self.update_rendered_view()
            # This line ensures the button resets to "Saved" on file load
            self.update_save_button_style()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load file:\n{str(e)}"
            )
            self.editor.clear()
            self.render_html.setHtml("")
            self.current_file = None
            self.original_content = ""
            self.has_unsaved_changes = False
            self.update_window_title()
            # Also update the button in case of an error
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

    def update_save_button_style(self):
        """Updates the save button's text and color based on save state."""
        if self.has_unsaved_changes:
            self.save_button.setText("Save (Ctrl+S)")
            # An orange color to indicate unsaved changes
            self.save_button.setStyleSheet("background-color: #fd7e14; color: #ffffff;")
        else:
            self.save_button.setText("Saved")
            # A green color to indicate the file is saved
            self.save_button.setStyleSheet("background-color: #28a745; color: #ffffff;")

    # Rendering?
    def update_rendered_view(self):
        """Update the rendered HTML view with current content and styling."""
        md_text = self.editor.toPlainText()
        
        if md_text.strip().lower().startswith('<!doctype html'):
            return

        custom_css = self.style_editor.toPlainText()

        try:
            base_dir = os.path.dirname(os.path.abspath(self.current_file)) if self.current_file else os.path.abspath(".")
            
            # Pass project_root to the renderer
            temp_html_path = render.markdown_to_html(md_text, custom_css, save_temp_file=True, base_dir=base_dir, project_root=self.project_root)
            
            if temp_html_path and os.path.exists(temp_html_path):
                from PyQt5.QtCore import QUrl
                file_url = QUrl.fromLocalFile(os.path.abspath(temp_html_path))
                
                query = f"v={int(time.time() * 1000)}"
                file_url.setQuery(query)
                
                self.render_html.setUrl(file_url)
            else:
                self.render_html.setHtml(temp_html_path or "")
                
        except Exception as e:
            error_html = f"<html><body><h3>Markdown Rendering Error</h3><p>{str(e)}</p></body></html>"
            self.render_html.setHtml(error_html)

    # Other
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
        self.showMaximized()

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

    # Menu System
    def _create_menu_bar(self):
        """Create the main menu bar for the application."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_current_file)

        new_menu = file_menu.addMenu("New")
        new_file_action = new_menu.addAction("New File")
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(self.handle_new_file_shortcut)

        new_folder_action = new_menu.addAction("New Folder")
        new_folder_action.triggered.connect(self.create_new_folder)

        delete_action = file_menu.addAction("Delete")
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)

        file_menu.addSeparator()

        # add exit button here

        # Document Menu
        document_menu = menu_bar.addMenu("&Document")

        front_matter_action = document_menu.addAction("Add Front Matter")
        front_matter_action.triggered.connect(self.add_front_matter)

        document_menu.addSeparator()

        paste_image_action = document_menu.addAction("Paste Image")
        paste_image_action.setShortcut("Ctrl+Shift+V")
        paste_image_action.triggered.connect(self.paste_image_from_clipboard)

        print_action = document_menu.addAction("Print Preview")
        print_action.triggered.connect(self.print_preview)


        # Utility Menu
        utility_menu = menu_bar.addMenu("&Utility")

        refresh_action = utility_menu.addAction("Refresh Tree")
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_tree_preserve_state)

        reset_style_action = utility_menu.addAction("Reset ALL Styles")
        reset_style_action.triggered.connect(self.reset_default_style)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        style_guide_action = help_menu.addAction("Styling Guide")
        style_guide_action.triggered.connect(
            lambda: self.open_help_file('docs/readme-css.md')
        )

        app_guide_action = help_menu.addAction("Application Guide")
        app_guide_action.triggered.connect(
            lambda: self.open_help_file('docs/readme.md')
        )
        
        help_menu.addSeparator()

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

    def open_help_file(self, file_path):
        """Load and display a read-only help file."""
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, "Help File Not Found", f"Could not find: {file_path}"
            )
            return

        self.load_file_by_path(file_path)
        if self.current_file == file_path:
            self.editor.setReadOnly(True)
            self.update_window_title()

    def update_window_title(self):
        """Update the main window title with file and save status."""
        title = "Markdown Manager"
        if self.current_file:
            # Check if it's a help file
            is_help_file = 'docs' in self.current_file.split(os.sep)
            filename = os.path.basename(self.current_file)
            status = " [Read-Only]" if is_help_file else ""
            title = f"{filename}{status} - {title}"

        if self.has_unsaved_changes:
            title = f"*{title}"

        self.setWindowTitle(title)

    def show_about_dialog(self):
        """Displays the application's About dialog."""
        try:
            version = self.config_manager.app_version
        except AttributeError:
            version = "Not Found"
        
        QMessageBox.about(
            self,
            "About Markdown Manager",
            f"""<b>Markdown Manager</b>
            <p>Version: {version}</p>
            <p>A lightweight, cross-platform Markdown editor and file manager built with PyQt5.</p>
            <p>For more information, see the Application Guide in the Help menu.</p>
            """
        )

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

    def get_main_window(self):
        """Get reference to the main window"""
        parent = self.parent()
        while parent and not hasattr(parent, 'add_lazy_children'):
            parent = parent.parent()
        return parent

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
        """Restore expanded state for given paths with proper lazy loading"""
        if not expanded_paths:
            return
        
        # Convert to list and sort by depth (shorter paths first)
        # This ensures parent directories are expanded before children
        paths_by_depth = sorted(expanded_paths, key=lambda p: p.count(os.sep))
        
        for target_path in paths_by_depth:
            if not os.path.exists(target_path):
                continue
                
            item = self.find_item_by_path(target_path)
            if not item:
                continue
            
            # Ensure all parent items are expanded first
            parent_items = []
            current_item = item.parent()
            while current_item:
                parent_items.insert(0, current_item)
                current_item = current_item.parent()
            
            # Expand parents first, triggering lazy loading as needed
            for parent_item in parent_items:
                if not parent_item.isExpanded():
                    # Check if needs lazy loading
                    if (parent_item.childCount() == 1 and 
                        parent_item.child(0).text(0) == "Loading..."):
                        parent_item.removeChild(parent_item.child(0))
                        parent_path = self.get_full_path(parent_item)
                        if parent_path and os.path.isdir(parent_path):
                            main_window = self.get_main_window()
                            if main_window:
                                main_window.add_lazy_children(parent_item, parent_path)
                    
                    parent_item.setExpanded(True)
            
            # Now expand the target item itself
            if not item.isExpanded():
                # Check if needs lazy loading
                if (item.childCount() == 1 and 
                    item.child(0).text(0) == "Loading..."):
                    item.removeChild(item.child(0))
                    item_path = self.get_full_path(item)
                    if item_path and os.path.isdir(item_path):
                        main_window = self.get_main_window()
                        if main_window:
                            main_window.add_lazy_children(item, item_path)
                
                item.setExpanded(True)
        
        # Force visual update
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
            # Store expanded state of all descendants, not just direct children
            descendant_expanded_state = {}
            
            def collect_expanded_state(item, state_dict):
                item_path = self.get_full_path(item)
                if item_path and item.isExpanded():
                    state_dict[item_path] = True
                
                for i in range(item.childCount()):
                    child = item.child(i)
                    if child.text(0) != "Loading...":
                        collect_expanded_state(child, state_dict)
            
            collect_expanded_state(dir_item, descendant_expanded_state)
            
            # Store the main directory's expanded state
            was_expanded = dir_item.isExpanded()
            
            # Clear all children
            dir_item.takeChildren()
            
            # Get current directory contents from filesystem
            items = []
            try:
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if os.path.isdir(item_path) or item_path.endswith(".md"):
                        items.append((item, item_path, os.path.isdir(item_path)))
            except (PermissionError, OSError) as e:
                error_item = QTreeWidgetItem([f"⚠ Error: Access Denied"])
                dir_item.addChild(error_item)
                return False
            
            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x[2], x[0].lower()))
            
            # Create new tree items
            for item_name, item_path, is_dir in items:
                if is_dir:
                    display_name = f"📁 {item_name}"
                else:
                    display_name = f"📄 {item_name}"
                    
                tree_item = QTreeWidgetItem([display_name])
                tree_item.setData(0, Qt.UserRole, item_path)
                dir_item.addChild(tree_item)
                
                # Add placeholder for directories that have children
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
                        pass
            
            # Restore main directory expanded state first
            if was_expanded:
                dir_item.setExpanded(True)
            
            # Restore expanded state for descendants
            if descendant_expanded_state:
                # Use a small delay to ensure tree is fully rendered
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, lambda: self.restore_expanded_state(descendant_expanded_state))
            
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
            
            # Perform selective refresh of affected directories
            if main_window:
                try:
                    # First, ensure the target directory is properly expanded and refreshed
                    target_item_path = target_path
                    target_tree_item = self.find_item_by_path(target_item_path)
                    
                    if target_tree_item:
                        # Force reload of target directory by clearing and reloading its children
                        target_tree_item.takeChildren()
                        
                        # Check if target has any children
                        has_children = False
                        try:
                            for item in os.listdir(target_item_path):
                                item_path = os.path.join(target_item_path, item)
                                if os.path.isdir(item_path) or item_path.endswith(".md"):
                                    has_children = True
                                    break
                        except (PermissionError, OSError):
                            pass
                        
                        if has_children:
                            # Add actual children instead of placeholder
                            main_window.add_lazy_children(target_tree_item, target_item_path)
                            
                            # Ensure the target directory is expanded to show the moved item
                            if not target_tree_item.isExpanded():
                                target_tree_item.setExpanded(True)
                    
                    # Also refresh the source directory if it still exists and is different from target
                    if source_dir != target_path and os.path.isdir(source_dir):
                        source_tree_item = self.find_item_by_path(source_dir)
                        if source_tree_item:
                            source_tree_item.takeChildren()
                            
                            # Check if source has any remaining children
                            has_children = False
                            try:
                                for item in os.listdir(source_dir):
                                    item_path = os.path.join(source_dir, item)
                                    if os.path.isdir(item_path) or item_path.endswith(".md"):
                                        has_children = True
                                        break
                            except (PermissionError, OSError):
                                pass
                            
                            if has_children:
                                main_window.add_lazy_children(source_tree_item, source_dir)
                    
                    # Restore expanded state for previously expanded paths
                    for path in expanded_paths:
                        if os.path.exists(path):  # Only restore if path still exists
                            item = self.find_item_by_path(path)
                            if item:
                                item.setExpanded(True)
                    
                    # Select the moved item in its new location
                    moved_item = self.find_item_by_path(new_path)
                    if moved_item:
                        self.setCurrentItem(moved_item)
                        self.scrollToItem(moved_item)
                        
                        # Ensure parent is expanded to show the moved item
                        parent_item = moved_item.parent()
                        if parent_item and not parent_item.isExpanded():
                            parent_item.setExpanded(True)
                    elif current_selection_path and os.path.exists(current_selection_path):
                        # If we can't find the moved item, restore previous selection if it still exists
                        selection_item = self.find_item_by_path(current_selection_path)
                        if selection_item:
                            self.setCurrentItem(selection_item)
                            self.scrollToItem(selection_item)
                    
                    # Force UI update
                    self.update()
                    if main_window:
                        main_window.update()
                    
                    print(f"Successfully moved {source_path} to {new_path}")
                    
                except Exception as refresh_error:
                    print(f"Selective refresh failed: {refresh_error}")
                    # If selective refresh fails, do a full tree reload as fallback
                    main_window.load_tree(".")
                    
                    # After full refresh, still try to restore state
                    self.restore_expanded_state(expanded_paths)
                    
                    # Try to select the moved item
                    moved_item = self.find_item_by_path(new_path)
                    if moved_item:
                        self.setCurrentItem(moved_item)
                        self.scrollToItem(moved_item)
                        # Ensure parent is visible
                        parent_item = moved_item.parent()
                        if parent_item:
                            parent_item.setExpanded(True)
            
            event.acceptProposedAction()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to move item:\n{str(e)}")
            event.ignore()

