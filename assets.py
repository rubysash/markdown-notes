# assets.py

"""
This module contains static assets, such as SVG icon data and stylesheets,
to be used by the application's GUI.
"""

SVG_ICON_CASE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#f0f0f0">
  <path d="M6.7,15.42,8.1,11.2h2.9l1.4,4.22H14L9.8,4.9H8.4L4,15.42Zm2-5.5-1.12-3.3c-.14-.42-.28-.88-.38-1.42H7.1c-.1.54-.24,1-.38,1.42L5.6,9.92ZM18.5,15.42V12.7h-3V11.3h3V8.6h1.4v2.7h3v1.4h-3v2.72Z"/>
</svg>
"""

SVG_ICON_SEARCH = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#f0f0f0">
  <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
</svg>
"""

SVG_ICON_CLEAR = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ff6b6b">
  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
</svg>
"""

ICON_BUTTON_STYLE = """
    QPushButton {
        border: 1px solid transparent;
        border-radius: 4px;
        background-color: transparent;
        padding: 2px;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
    }
    QPushButton:pressed {
        background-color: #4a4a4a;
    }
    QPushButton:checked {
        background-color: #007bff;
        border: 1px solid #0056b3;
    }
"""