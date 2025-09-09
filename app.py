# app.py

import sys
from PyQt5.QtWidgets import QApplication
from gui import MarkdownManagerApp
from config import ConfigManager

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize config manager
    config_manager = ConfigManager()
    
    # Load GUI styling from template file
    gui_css = config_manager.load_gui_css()
    app.setStyleSheet(gui_css)

    window = MarkdownManagerApp()
    window.run()
    sys.exit(app.exec_())