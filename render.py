# render.py

import markdown
import os
import sys
import re
import uuid
import html

def _load_template(file_name):
    """Loads a template file with error handling."""
    try:
        # Templates are expected to be in a 'templates' subdirectory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "templates", file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        print(f"Warning: Template file not found at {file_path}")
    except (IOError, OSError) as e:
        print(f"Warning: Could not load template file {file_name}: {e}")
    return ""  # Return empty string on failure

def process_svg_and_images(html_content, base_dir=None, project_root=None):
    """Process SVG elements and image paths, resolving root-relative links."""
    import re
    
    def fix_svg_element(match):
        """A simplified processor for inline SVGs."""
        svg_content = match.group(0)
        
        if 'xmlns=' not in svg_content:
            svg_content = svg_content.replace(
                '<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1
            )
        
        if 'style=' not in svg_content:
            web_style = 'max-width: 100%; height: auto; display: block; margin: 1em auto;'
            svg_content = svg_content.replace('<svg', f'<svg style="{web_style}"', 1)
            
        return svg_content

    html_content = re.sub(
        r'<svg[^>]*?>.*?</svg>', 
        fix_svg_element, 
        html_content, 
        flags=re.DOTALL | re.IGNORECASE
    )
    
    if base_dir and project_root:
        def fix_image_path(match):
            img_tag = match.group(0)
            src_match = re.search(r'src="([^"]+)"', img_tag)
            if not src_match: return img_tag
            
            original_src = src_match.group(1)
            
            if original_src.startswith(('http', 'data:', 'file:///')):
                return img_tag
            
            absolute_path = None
            if original_src.startswith('/'):
                # It's a root-relative path, join with project_root
                absolute_path = os.path.normpath(os.path.join(project_root, original_src[1:]))
            else:
                # It's a standard relative path, join with base_dir
                absolute_path = os.path.normpath(os.path.join(base_dir, original_src))

            if absolute_path and os.path.exists(absolute_path):
                file_url = f"file:///{absolute_path.replace(os.sep, '/')}"
                return img_tag.replace(f'src="{original_src}"', f'src="{file_url}"')
            
            return img_tag

        html_content = re.sub(r'<img[^>]+src="[^"]+"', fix_image_path, html_content)
    
    return html_content

def get_svg_support_css():
    """Return CSS specifically for SVG support from a template file."""
    return _load_template("svg_support.tpl")

def markdown_to_html(md_text, custom_css=None, save_temp_file=False, base_dir=None, project_root=None):
    """
    Converts markdown to HTML, safely protecting and re-inserting SVG blocks.
    """
    css_manager = CSSManager()
    
    try:
        # 1. Protect SVG by extracting it and leaving a unique text placeholder
        placeholders = {}
        def extract_svg_callback(match):
            placeholder = f"svg-placeholder-{uuid.uuid4()}"
            placeholders[placeholder] = match.group(0)
            return placeholder
        
        md_text_clean = re.sub(
            r'<svg.*?</svg>',
            extract_svg_callback,
            md_text,
            flags=re.DOTALL | re.IGNORECASE
        )

        # 2. Configure and run the Markdown processor
        extensions = [
            'tables', 'fenced_code', 'sane_lists', 'codehilite',
            'toc', 'extra', 'attr_list'
        ]
        extension_configs = {
            'codehilite': {'css_class': 'highlight', 'use_pygments': True}
        }
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
            output_format='html5'
        )
        html_content = md.convert(md_text_clean)

        # 3. Re-insert the original SVG content
        for placeholder, svg_block in placeholders.items():
            # The placeholder might be wrapped in <p> tags by the processor
            p_placeholder = f"<p>{placeholder}</p>"
            if p_placeholder in html_content:
                html_content = html_content.replace(p_placeholder, svg_block)
            else:
                html_content = html_content.replace(placeholder, svg_block)

        # 4. Post-process the final HTML to resolve image paths
        html_content = process_svg_and_images(html_content, base_dir, project_root)

        # 5. Assemble the full HTML page
        preview_css = css_manager.get_preview_css(custom_css)
        svg_css = get_svg_support_css()
        html_full_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Markdown Preview</title>
    <style>{preview_css}\n{svg_css}</style>
</head>
<body>{html_content}</body>
</html>"""

        # 6. Save to temp file for the viewer
        if save_temp_file and base_dir:
            temp_file_path = os.path.join(base_dir, '.markdown_preview_temp.html')
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(html_full_page)
            return temp_file_path
        
        return html_full_page

    except Exception as e:
        return _generate_error_html(f"Failed to render markdown: {str(e)}")

def _generate_error_html(error_message):
    """Generate a styled error HTML page"""
    error_css = _load_template("error.tpl")
    
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
        <div class="error-message">{html.escape(error_message)}</div>
        <div class="error-suggestion">
            Please check your markdown syntax and try again. 
            If the problem persists, verify that all required Python packages are installed.
        </div>
    </div>
</body>
</html>"""

def markdown_to_html_for_browser_print(md_text, print_css="", source_file_path=None, project_root=None):
    """Convert markdown to HTML for browser printing with SVG and image support"""
    try:
        import markdown
        import os
        
        # 1. Protect SVG by extracting it and leaving a unique text placeholder
        placeholders = {}
        def extract_svg_callback(match):
            placeholder = f"svg-placeholder-{uuid.uuid4()}"
            placeholders[placeholder] = match.group(0)
            return placeholder
        
        md_text_clean = re.sub(
            r'<svg.*?</svg>',
            extract_svg_callback,
            md_text,
            flags=re.DOTALL | re.IGNORECASE
        )

        # 2. Configure and run the Markdown processor
        extensions = [
            'extra', 'codehilite', 'toc', 'tables', 'fenced_code', 'attr_list'
        ]
        extension_configs = {
            'codehilite': {'css_class': 'highlight', 'use_pygments': True}
        }
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
            output_format='html5'
        )
        html_body = md.convert(md_text_clean)

        # 3. Re-insert the original SVG content
        for placeholder, svg_block in placeholders.items():
            p_placeholder = f"<p>{placeholder}</p>"
            if p_placeholder in html_body:
                html_body = html_body.replace(p_placeholder, svg_block)
            else:
                html_body = html_body.replace(placeholder, svg_block)

        # 4. Wrap the final SVG in an Iframe to isolate it from print CSS
        def wrap_svg_in_iframe(match):
            svg_code = match.group(0)
            # Escape for use in the srcdoc attribute
            escaped_svg = html.escape(svg_code)
            # Use vh for a responsive height and a simple border
            style = "width: 100%; height: 80vh; border: 1px solid #eee; margin: 1em auto; display: block;"
            return f'<iframe style="{style}" srcdoc="{escaped_svg}"></iframe>'

        html_body = re.sub(
            r'<svg.*?</svg>', 
            wrap_svg_in_iframe, 
            html_body, 
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # 5. Process standard images for print
        html_body = process_svg_and_images_for_print(html_body, source_file_path, project_root)
        
        # Get title from first h1 or use filename
        title = "Markdown Document"
        if source_file_path:
            title = os.path.splitext(os.path.basename(source_file_path))[0]
        
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_body)
        if h1_match:
            title = h1_match.group(1).strip()
        
        # Create complete HTML document
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} - Print</title>
    <style>{print_css}</style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
        return html_content
        
    except Exception as e:
        print(f"Error in markdown_to_html_for_browser_print: {str(e)}")
        return f"<html><body><h1>Error</h1><p>Failed to render markdown: {html.escape(str(e))}</p></body></html>"

def process_svg_and_images_for_print(html_content, source_file_path=None, project_root=None):
    """Process images for print, resolving root-relative links."""
    import re
    import os
    
    def fix_svg_for_print(match):
        svg_content = match.group(0)
        if 'xmlns=' not in svg_content:
            svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        return svg_content
    
    html_content = re.sub(r'<svg[^>]*>.*?</svg>', fix_svg_for_print, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    def fix_image_for_print(match):
        img_tag = match.group(0)
        src_match = re.search(r'src="([^"]+)"', img_tag)
        if not src_match: return img_tag
        
        original_src = src_match.group(1)
        
        if original_src.startswith(('http', 'https-:', 'data:', 'file:///')):
            return img_tag
        
        absolute_path = None
        base_dir = os.path.dirname(os.path.abspath(source_file_path)) if source_file_path else project_root
        
        if not base_dir: return img_tag

        if original_src.startswith('/'):
            # Root-relative path
            if not project_root: return img_tag
            absolute_path = os.path.normpath(os.path.join(project_root, original_src[1:]))
        else:
            # Standard relative path
            absolute_path = os.path.normpath(os.path.join(base_dir, original_src))

        if absolute_path and os.path.exists(absolute_path):
            file_url = f"file:///{absolute_path.replace(os.sep, '/')}"
            return img_tag.replace(f'src="{original_src}"', f'src="{file_url}"')
        
        return img_tag
    
    html_content = re.sub(r'<img[^>]+>', fix_image_for_print, html_content)
    
    return html_content

def get_print_svg_css():
    """Return CSS specifically for SVG support in print output with better sizing control"""
    return _load_template("print_svg_support.tpl")

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
                
                if in_section:
                    # Append the line, preserving indentation
                    css_lines.append(line)
            
            # Reconstruct content from the correct point
            if css_lines:
                # Find the start of content after the marker
                full_text = '\n'.join(css_lines)
                content_start = full_text.find(section_marker)
                if content_start != -1:
                    css_content = full_text[content_start + len(section_marker):].strip()
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
        return _load_template("fallback_preview.tpl")