# render.py

import markdown
import os
import sys

class CSSManager:
    """Manages CSS loading with simple two-layer fallback system"""
    
    def __init__(self):
        self.config_manager = None
        self._init_config_manager()
    
    def _init_config_manager(self):
        """Initialize config manager with error handling"""
        try:
            from config import ConfigManager
            self.config_manager = ConfigManager()
        except ImportError as e:
            print(f"Warning: Could not import ConfigManager: {e}")
    
    def extract_css_from_config(self, config_content, section_name="Preview"):
        """Extract CSS content from a configuration section"""
        if not config_content or not config_content.strip():
            return None
            
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
                
                if line_stripped.startswith('[') and line_stripped.endswith(']'):
                    if line_stripped != section_marker:
                        in_section = False
                        continue
                
                if in_section:
                    if not line_stripped.startswith('#') and line_stripped:
                        css_lines.append(line)
                    elif not line_stripped:
                        css_lines.append(line)
            
            if css_lines:
                css_content = '\n'.join(css_lines).strip()
                if css_content and len(css_content) > 10:
                    return css_content
                
        except Exception as e:
            print(f"Warning: Failed to extract CSS from config: {e}")
        
        return None
    
    def get_preview_css(self, custom_css=None):
        """Get preview CSS with simple fallback chain"""
        
        if custom_css and custom_css.strip():
            css_content = self.extract_css_from_config(custom_css, "Preview")
            if css_content:
                return css_content
        
        if self.config_manager:
            try:
                css_content = self.config_manager.load_preview_css()
                if css_content and css_content.strip():
                    return css_content
            except Exception as e:
                print(f"Warning: ConfigManager preview CSS loading failed: {e}")
        
        return self.get_emergency_fallback_css()
    
    def get_emergency_fallback_css(self):
        """Emergency CSS when all else fails"""
        return """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    background-color: #212529;
    color: #aaa;
    padding: 20px;
    margin: 0;
    line-height: 1.6;
    font-size: 16px;
}
h1, h2, h3, h4, h5, h6 { 
    color: #ffffff; 
    margin: 1.5em 0 1em 0;
    font-weight: 600;
}
h1 { font-size: 2.5rem; border-bottom: 2px solid #495057; padding-bottom: 0.75rem; }
h2 { font-size: 2rem; color: #ff6b6b; }
h3 { font-size: 1.5rem; color: #007bff; }
p { margin-bottom: 1rem; color: #ffffff; }
code { 
    background-color: #343a40; 
    color: #fd7e14; 
    padding: 0.25rem 0.5rem; 
    border-radius: 0.375rem;
    font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace; 
    font-size: 0.875em;
}
pre { 
    background-color: #1e2125; 
    border: 1px solid #495057;
    padding: 1.25rem; 
    overflow-x: auto; 
    margin: 1.5rem 0;
    border-radius: 0.5rem;
}
pre code {
    background: none;
    color: #e9ecef;
    padding: 0;
    border: none;
}
blockquote {
    border-left: 4px solid #007bff;
    margin: 1.5rem 0;
    padding: 1rem 1.5rem;
    background-color: #343a40;
    color: #ced4da;
    font-style: italic;
}
"""

def markdown_to_html(md_text, custom_css=None, save_temp_file=False, base_dir=None):
    """Convert markdown text to HTML with optional custom CSS"""
    css_manager = CSSManager()
    
    try:
        extensions = [
            'tables',
            'fenced_code',
            'nl2br',
            'sane_lists',
            'codehilite',
            'toc',
        ]
        
        extension_configs = {
            'sane_lists': {},
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
            },
            'toc': {
                'permalink': True,
            }
        }
        
        html_content = markdown.markdown(
            md_text, 
            extensions=extensions,
            extension_configs=extension_configs
        )
        
        # Fix image paths to be absolute for preview
        if base_dir:
            import re
            import sys

            def fix_image_path(match):
                img_tag = match.group(0)
                src_match = re.search(r'src="([^"]+)"', img_tag)
                if not src_match:
                    return img_tag
                
                original_src = src_match.group(1)

                # Skip external URLs and file:///
                if original_src.startswith(('http://', 'https://', 'file:///')):
                    return img_tag

                # Resolve root-relative paths like /images/foo.png
                if original_src.startswith('/images/'):
                    try:
                        app_root_dir = os.path.abspath(os.path.dirname(sys.modules['__main__'].__file__))
                        absolute_path = os.path.join(app_root_dir, original_src.lstrip('/'))
                        if os.path.exists(absolute_path):
                            file_url = f"file:///{absolute_path.replace(os.sep, '/')}"
                            return img_tag.replace(f'src="{original_src}"', f'src="{file_url}"')
                    except Exception as e:
                        print(f"Failed to resolve /images/ path: {e}")
                    return img_tag  # fallback

                # For other relative paths (e.g., images/foo.png or ../images/foo.png)
                absolute_path = os.path.normpath(os.path.join(base_dir, original_src))
                if os.path.exists(absolute_path):
                    file_url = f"file:///{absolute_path.replace(os.sep, '/')}"
                    return img_tag.replace(f'src="{original_src}"', f'src="{file_url}"')
                
                return img_tag  # fallback if not found

            html_content = re.sub(r'<img[^>]+>', fix_image_path, html_content)
        
        preview_css = css_manager.get_preview_css(custom_css)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Preview</title>
    <style>{preview_css}</style>
</head>
<body>
{html_content}
</body>
</html>"""

        if save_temp_file and base_dir:
            import tempfile
            temp_file = os.path.join(base_dir, '.markdown_preview_temp.html')
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                return temp_file
            except Exception as e:
                print(f"Failed to write temp file: {e}")
                return html
        
        return html
        
    except ImportError as e:
        try:
            basic_extensions = ['tables', 'fenced_code']
            html_content = markdown.markdown(
                md_text, 
                extensions=basic_extensions
            )
            preview_css = css_manager.get_preview_css(custom_css)
            
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Preview</title>
    <style>{preview_css}</style>
</head>
<body>
{html_content}
</body>
</html>"""

            if save_temp_file and base_dir:
                import tempfile
                temp_file = os.path.join(base_dir, '.markdown_preview_temp.html')
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    return temp_file
                except Exception as e:
                    print(f"Failed to write temp file: {e}")
                    return html
            
            return html
        except Exception as fallback_error:
            return _generate_error_html(f"Markdown processing failed: {fallback_error}")
    
    except Exception as e:
        return _generate_error_html(f"Error rendering markdown: {e}")

def _generate_error_html(error_message):
    """Generate a styled error HTML page"""
    error_css = """
body { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; 
    background-color: #121212; 
    color: #f0f0f0; 
    padding: 20px; 
    margin: 0; 
    line-height: 1.6;
}
.error-container { 
    background-color: #2c1e1e; 
    border: 1px solid #e74c3c; 
    border-radius: 8px; 
    padding: 24px; 
    margin: 20px 0; 
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.error-title { 
    color: #e74c3c; 
    font-size: 1.4em; 
    font-weight: 600; 
    margin-bottom: 12px; 
    margin-top: 0;
}
.error-message { 
    color: #f0f0f0; 
    line-height: 1.6; 
    margin-bottom: 12px;
    font-family: monospace;
    background-color: #1a1a1a;
    padding: 12px;
    border-radius: 4px;
    border-left: 4px solid #e74c3c;
}
.error-suggestion { 
    color: #bdc3c7; 
    font-style: italic; 
    margin-top: 16px; 
    padding-top: 12px;
    border-top: 1px solid #495057;
}
"""
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Error</title>
    <style>{error_css}</style>
</head>
<body>
    <div class="error-container">
        <h2 class="error-title">Markdown Rendering Error</h2>
        <div class="error-message">{error_message}</div>
        <div class="error-suggestion">
            Please check your markdown syntax and try again. 
            If the problem persists, verify that all required Python packages are installed.
        </div>
    </div>
</body>
</html>"""

def del_markdown_to_html_for_print(md_text, print_css=""):
    """Convert markdown to HTML specifically optimized for printing"""
    import time
    import hashlib
    
    try:
        import markdown
        
        # Configure markdown extensions for print
        extensions = [
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code'
        ]
        
        extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True
            }
        }
        
        # Create markdown instance
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs
        )
        
        # Convert markdown to HTML
        html_body = md.convert(md_text)
        
        # Create a hash of the CSS for cache busting
        css_hash = hashlib.md5(print_css.encode('utf-8')).hexdigest()[:8] if print_css else "default"
        timestamp = int(time.time())
        
        # Ensure we have some CSS
        if not print_css or len(print_css) < 100:
            print("Warning: Using minimal fallback CSS for print")
            print_css = """
            body { font-family: Arial, sans-serif; font-size: 12pt; color: black; background: white; }
            h1 { font-size: 20pt; }
            h2 { font-size: 16pt; }
            h3 { font-size: 14pt; }
            h4 { font-size: 12pt; }
            p, li { font-size: 12pt; }
            strong, b { font-size: inherit; font-weight: bold; }
            """
        
        # Add cache-busting comment to CSS
        cache_busted_css = f"/* Cache: {css_hash}-{timestamp} */\n{print_css}"
        
        # Create complete HTML document with print CSS embedded
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Print Document</title>
    <style>
        {cache_busted_css}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
        print(f"Generated print HTML with CSS hash: {css_hash}")
        return html_content
        
    except ImportError:
        # Fallback if markdown not available
        html_body = md_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
        html_body = f"<p>{html_body}</p>"
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Print Document</title>
    <style>
        {print_css if print_css else "body { font-family: Arial, sans-serif; font-size: 12pt; }"}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
    except Exception as e:
        print(f"Error in markdown_to_html_for_print: {str(e)}")
        # Return simple fallback
        html_body = md_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
        html_body = f"<p>{html_body}</p>"
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Print Document</title>
    <style>
        {print_css if print_css else "body { font-family: Arial, sans-serif; font-size: 12pt; }"}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
    
def markdown_to_html_for_browser_print(md_text, print_css="", source_file_path=None):
    """Convert markdown to HTML for browser printing with image support"""
    try:
        import markdown
        import os
        
        # Configure markdown extensions for print
        extensions = [
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code'
        ]
        
        extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True
            }
        }
        
        # Create markdown instance
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs
        )
        
        # Convert markdown to HTML
        html_body = md.convert(md_text)
        
        # Fix image paths to be relative to the source file
        if source_file_path:
            source_dir = os.path.dirname(os.path.abspath(source_file_path))
            
            # Find and fix image references
            import re
            def fix_image_path(match):
                img_tag = match.group(0)
                src_match = re.search(r'src="([^"]+)"', img_tag)
                if src_match:
                    original_src = src_match.group(1)
                    
                    # Skip if already absolute path or URL
                    if original_src.startswith(('http://', 'https://', 'file://', '/')):
                        return img_tag
                    
                    # Convert relative path to absolute path
                    absolute_path = os.path.join(source_dir, original_src)
                    if os.path.exists(absolute_path):
                        file_url = f"file:///{absolute_path.replace(os.sep, '/')}"
                        return img_tag.replace(f'src="{original_src}"', f'src="{file_url}"')
                    else:
                        # Image not found, add a note
                        return f'<div style="border: 1px dashed #ccc; padding: 12pt; margin: 6pt 0; text-align: center; font-style: italic; color: #666;">[Image not found: {original_src}]</div>'
                
                return img_tag
            
            html_body = re.sub(r'<img[^>]+>', fix_image_path, html_body)
        
        # Get title from first h1 or use filename
        title = "Markdown Document"
        if source_file_path:
            title = os.path.splitext(os.path.basename(source_file_path))[0]
        
        # Look for first h1 in content
        import re
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_body)
        if h1_match:
            title = h1_match.group(1)
        
        # Create complete HTML document using provided CSS
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Print</title>
    <style>
        {print_css}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
        return html_content
        
    except ImportError:
        # Fallback if markdown not available
        html_body = md_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
        html_body = f"<p>{html_body}</p>"
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Print Document</title>
    <style>
        {print_css if print_css else "body { font-family: Arial; font-size: 12pt; }"}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
    except Exception as e:
        print(f"Error in markdown_to_html_for_browser_print: {str(e)}")
        return f"<html><body><h1>Error</h1><p>Failed to render markdown: {str(e)}</p></body></html>"