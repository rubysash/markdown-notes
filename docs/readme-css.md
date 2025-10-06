---
title: "Your Title Here"
date: 2025-07-15
draft: false
tags: []
categories: []
description: "Brief description"
---


## CSS Files

### Default/Fallback

| File | Purpose | Key Features |
|------|---------|--------------|
| `gui.tpl` | GUI styling master template | Source template copied to css/user/gui.css on first run and reset |
| `preview.tpl` | Preview styling master template | Source template copied to css/user/preview.css on first run and reset |

### User Customization

```
css/
└── user/              # Your customizations (actively used)
    ├── gui.css               # Current GUI styling (what you see)
    └── preview.css           # Current preview styling (what you see)
```
### Configuration Management
- **Direct Template Usage**: Uses `.tpl` files as the master source for all default styles
- **Simplified Structure**: Only `css/user/` directory contains actively used files
- **Live CSS Editing**: Style tab provides real-time editing with immediate preview updates
- **Template-Based Reset**: Reset function copies directly from `.tpl` files to user directory
- **Emergency Fallback**: Embedded CSS in `render.py` ensures application never fails to render

## How the CSS System Actually Works

### Initial Setup (First Run)
- Application checks if `css/user/` directory exists
- If not, creates the directory structure
- Copies `gui.tpl` → `css/user/gui.css`
- Copies `preview.tpl` → `css/user/preview.css`
- Creates `css/defaults/` directory structure (for potential future use)

### Daily Usage
- Application reads directly from: `css/user/gui.css` and `css/user/preview.css`
- Style editor modifies: `css/user/gui.css` and `css/user/preview.css`
- Reset button restores: Copies from template files (`gui.tpl`, `preview.tpl`) back to `css/user/`

### Template Files (.tpl)
- `gui.tpl`: Master template for PyQt5 application styling
- `preview.tpl`: Master template for markdown HTML rendering
- These are the actual source of truth for default styles

### Fallback Chain
If a file is missing, the system falls back in this order:
1. `css/user/preview.css` (your active customizations)
2. `gui.tpl` or `preview.tpl` (master templates)
3. Embedded emergency CSS (hardcoded minimal styles in render.py)


# Style Customization Guide

The application includes powerful features for customizing its entire look and feel. These features are managed through the "Style" tab and the "Reset Style" button.

### The "Style" Tab 🎨

The **"Style" tab** is a built-in code editor that allows you to directly modify the Cascading Style Sheets (CSS) that control the application's appearance. Your custom styles are loaded from and saved to files within the `css/user/` directory.

The style editor manages three distinct parts of the application, separated by headers:

* **`[Preview]`**: This section controls the appearance of your rendered markdown in the **"Preview" tab**.
    * You can change fonts, colors, code block styling, and more.
    * The default styles for the preview are defined in `preview.tpl`.
    * Any changes you make in the editor under this section will **update the preview in real-time**.

* **`[GUI]`**: This section styles the **main application interface** itself.
    * This includes the file tree, buttons, tabs, and text boxes.
    * The application's default dark theme is defined in the `gui.tpl` file.
    * To see changes made here, you must **save the style configuration** (`Ctrl+S` while on the Style tab) and restart the application.

* **`[Print]`**: This section contains CSS specifically for the **"Print Preview"** feature.
    * It formats the document for printing, optimizing it for a standard paper layout.
    * This allows you to have a dark theme for editing but a clean, light theme for printed output.

To make your style changes permanent, you must press the **Save File button** or `Ctrl+S` while the "Style" tab is active. This action saves your modifications to the appropriate `.css` files in the `css/user/` folder.

### The "Reset Style" Button 🔄

The **"Reset Style" button** provides a simple way to revert all appearance customizations back to their original state.

When you click this button and confirm the action, the application performs the following steps:
1.  It reads the default CSS from the template files (`preview.tpl`, `gui.tpl`, and a print template).
2.  It overwrites your custom CSS files (e.g., `preview.css`, `gui.css`) with the default content.
3.  It updates the "Style" tab with the default code.

This is a useful feature if you've made changes you don't like and want to quickly return to the application's standard theme.