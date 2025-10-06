# config.py

import os
from datetime import datetime

class ConfigManager:
    def __init__(self):
        self.app_version = "1.0.0"
        self.user_css_dir = "css/user"
        self.preview_css_file = os.path.join(self.user_css_dir, "preview.css")
        self.gui_css_file = os.path.join(self.user_css_dir, "gui.css")
        self.print_css_file = os.path.join(self.user_css_dir, "print.css")
        # paths look inside the 'templates' folder
        self.preview_template = os.path.join("templates", "preview.tpl")
        self.gui_template = os.path.join("templates", "gui.tpl")
        self.print_template = os.path.join("templates", "print.tpl")
        self.front_matter_template = self.get_default_front_matter()
        self.ensure_css_structure()
    
    def ensure_css_structure(self):
        """Create user CSS directory and initialize with templates if needed"""
        try:
            os.makedirs(self.user_css_dir, exist_ok=True)
            
            # Initialize print CSS if it doesn't exist
            if not os.path.exists(self.print_css_file):
                print_template_content = self._load_css_from_file(self.print_template)
                if print_template_content:
                    self._save_css_to_file(self.print_css_file, print_template_content)
            
            # Initialize preview CSS if it doesn't exist
            if not os.path.exists(self.preview_css_file):
                preview_template_content = self._load_css_from_file(self.preview_template)
                if preview_template_content:
                    self._save_css_to_file(self.preview_css_file, preview_template_content)
            
            # Initialize GUI CSS if it doesn't exist
            if not os.path.exists(self.gui_css_file):
                gui_template_content = self._load_css_from_file(self.gui_template)
                if gui_template_content:
                    self._save_css_to_file(self.gui_css_file, gui_template_content)
                    
        except Exception as e:
            print(f"Error creating CSS directory structure: {e}")
    
    def _load_css_from_file(self, filepath):
        """Load CSS content from file with error handling"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content and len(content) > 10:
                        return content
        except Exception as e:
            print(f"Error loading CSS from {filepath}: {e}")
        return None
    
    def _save_css_to_file(self, filepath, content):
        """Save CSS content to file with error handling"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving CSS to {filepath}: {e}")
            return False
    
    def load_preview_css(self):
        """Load preview CSS from user file with fallback to template"""
        css_content = self._load_css_from_file(self.preview_css_file)
        if css_content is None:
            css_content = self._load_css_from_file(self.preview_template)
        return css_content or ""
    
    def load_gui_css(self):
        """Load GUI CSS from user file with fallback to template"""
        css_content = self._load_css_from_file(self.gui_css_file)
        if css_content is None:
            css_content = self._load_css_from_file(self.gui_template)
        return css_content or ""
    
    def load_print_css(self):
        """Load print CSS from template file with cache busting"""
        import time
        
        try:
            # First try to load from user print CSS file
            if os.path.exists(self.print_css_file):
                # Get file modification time to check if it's fresh
                mod_time = os.path.getmtime(self.print_css_file)
                current_time = time.time()
                
                # If file is older than template, refresh it
                template_path = os.path.join(os.path.dirname(__file__), 'templates', 'print.tpl')
                if os.path.exists(template_path):
                    template_mod_time = os.path.getmtime(template_path)
                    if template_mod_time > mod_time:
                        print(f"Template newer than user CSS, refreshing print CSS")
                        # Copy template to user file
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_content = f.read()
                        with open(self.print_css_file, 'w', encoding='utf-8') as f:
                            f.write(template_content)
                
                with open(self.print_css_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content and len(content) > 10:
                        return content
                    else:
                        print(f"WARNING: Loaded print CSS from user file: {self.print_css_file} is {len(content)} chars")
            
            # Fallback to template file in same directory as config.py
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'print.tpl')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Loaded print CSS from template: {len(content)} chars")
                    return content
            else:
                print(f"Warning: print.tpl not found at {template_path}")
                return ""
                
        except Exception as e:
            print(f"Error loading print CSS: {e}")
            return ""
    
    def save_preview_css(self, css_content):
        """Save preview CSS to user file"""
        return self._save_css_to_file(self.preview_css_file, css_content)
    
    def save_gui_css(self, css_content):
        """Save GUI CSS to user file"""
        return self._save_css_to_file(self.gui_css_file, css_content)
    
    def save_print_css(self, css_content):
        """Save print CSS to user file"""
        return self._save_css_to_file(self.print_css_file, css_content)
    
    def reset_preview_css_to_default(self):
        """Reset preview CSS by removing user override"""
        try:
            if os.path.exists(self.preview_css_file):
                os.remove(self.preview_css_file)
            return True
        except Exception as e:
            print(f"Error resetting preview CSS: {e}")
            return False
    
    def reset_gui_css_to_default(self):
        """Reset GUI CSS by removing user override"""
        try:
            if os.path.exists(self.gui_css_file):
                os.remove(self.gui_css_file)
            return True
        except Exception as e:
            print(f"Error resetting GUI CSS: {e}")
            return False
    
    def reset_print_css_to_default(self):
        """Reset print CSS by removing user override"""
        try:
            if os.path.exists(self.print_css_file):
                os.remove(self.print_css_file)
            return True
        except Exception as e:
            print(f"Error resetting print CSS: {e}")
            return False
    
    def reset_all_to_default(self):
        """Reset all CSS files to defaults"""
        preview_reset = self.reset_preview_css_to_default()
        gui_reset = self.reset_gui_css_to_default()
        print_reset = self.reset_print_css_to_default()
        return preview_reset and gui_reset and print_reset
    
    def load_config(self):
        """Load the combined configuration content for the style editor"""
        try:
            preview_css = self.load_preview_css()
            gui_css = self.load_gui_css()
            print_css = self.load_print_css()
            
            config_content = f"""# Style Configuration File
# This file contains CSS styling for Preview, GUI, and Print components
# Edit the sections below to customize the appearance

## Preview CSS (for markdown rendering)
[Preview]
{preview_css}

## GUI CSS (for application interface)
[GUI]
{gui_css}

## Print CSS (for printing - optimized for paper)
[Print]
{print_css}
"""
            return config_content
        except Exception as e:
            print(f"Error loading config: {e}")
            return "# Error loading configuration"
    
    def save_config(self, config_content):
        """Save the combined configuration content"""
        try:
            preview_css = self.extract_css_from_config(config_content, "Preview")
            gui_css = self.extract_css_from_config(config_content, "GUI")
            print_css = self.extract_css_from_config(config_content, "Print")
            
            preview_saved = self.save_preview_css(preview_css)
            gui_saved = self.save_gui_css(gui_css)
            print_saved = self.save_print_css(print_css)
            
            return preview_saved and gui_saved and print_saved
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def extract_css_from_config(self, config_content, section_name):
        """Extract CSS content from a specific section"""
        try:
            lines = config_content.split('\n')
            in_section = False
            css_lines = []
            section_marker = f"[{section_name}]"
            
            for line in lines:
                line_stripped = line.strip()
                
                if line_stripped == section_marker:
                    in_section = True
                    continue
                
                if line_stripped.startswith('[') and line_stripped.endswith(']') and line_stripped != section_marker:
                    in_section = False
                    continue
                
                if in_section and not line_stripped.startswith('#'):
                    css_lines.append(line)
            
            css_content = '\n'.join(css_lines).strip()
            
            if not css_content:
                if section_name == "Preview":
                    return self.load_preview_css()
                elif section_name == "GUI":
                    return self.load_gui_css()
                elif section_name == "Print":
                    return self.load_print_css()
            
            return css_content
            
        except Exception as e:
            print(f"Error extracting CSS from config: {e}")
            if section_name == "Preview":
                return self.load_preview_css()
            elif section_name == "GUI":
                return self.load_gui_css()
            elif section_name == "Print":
                return self.load_print_css()
            return ""
    
    def get_default_style(self):
        """Get the default combined style configuration"""
        try:
            default_preview = self._load_css_from_file(self.preview_template) or ""
            default_gui = self._load_css_from_file(self.gui_template) or ""
            default_print = self._load_css_from_file(self.print_template) or ""
            
            return f"""# Style Configuration File
# This file contains CSS styling for Preview, GUI, and Print components
# Edit the sections below to customize the appearance

## Preview CSS (for markdown rendering)
[Preview]
{default_preview}

## GUI CSS (for application interface)
[GUI]
{default_gui}

## Print CSS (for printing - optimized for paper)
[Print]
{default_print}
"""
        except Exception as e:
            print(f"Error getting default style: {e}")
            return "# Error loading default style"
    
    def get_default_front_matter(self):
        """Get front matter template with current date"""
        return """---
title: "Your Title Here"
date: {date}
draft: false
tags: []
categories: []
description: "Brief description"
---

"""
    
    def get_front_matter_template(self):
        """Get front matter template with current date"""
        return self.front_matter_template.format(date=self.get_current_date())
    
    def get_current_date(self):
        """Get current date in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_file_modification_time(self, filepath):
        """Get file modification time"""
        try:
            if os.path.exists(filepath):
                return os.path.getmtime(filepath)
            return 0
        except Exception:
            return 0
    
    def get_preview_css_mod_time(self):
        """Get preview CSS file modification time"""
        return self.get_file_modification_time(self.preview_css_file)
    
    def get_gui_css_mod_time(self):
        """Get GUI CSS file modification time"""
        return self.get_file_modification_time(self.gui_css_file)
    
    def get_print_css_mod_time(self):
        """Get print CSS file modification time"""
        return self.get_file_modification_time(self.print_css_file)