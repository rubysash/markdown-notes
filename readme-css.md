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
