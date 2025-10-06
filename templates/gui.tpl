/* Main Application UI Styling */
QWidget {
    background-color: #121212;
    color: #f0f0f0;
    font-family: Verdana, sans-serif;
    font-size: 13px;
}

QPlainTextEdit, QTreeWidget, QTabWidget::pane {
    background-color: #1f1f1f;
    border: 1px solid #333;
    font-size: 13px;
}

QHeaderView::section {
    background-color: #1f1f1f;
}

QTreeWidget::item:selected {
    background-color: #333333;
    color: #f0f0f0;
}

QTabBar::tab {
    background: #1f1f1f;
    color: #f0f0f0;
    padding: 6px;
    border: 1px solid #333;
    border-bottom: none;
    min-width: 80px;
}

QTabBar::tab:selected {
    background: #333333;
}

QTabBar::tab:!selected {
    background: #1f1f1f;
}

QPushButton {
    background-color: #1f1f1f;
    border: 1px solid #333;
    padding: 6px 12px;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #333333;
}

QPushButton:pressed {
    background-color: #444444;
}