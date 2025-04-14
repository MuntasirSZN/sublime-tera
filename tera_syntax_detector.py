import sublime
import sublime_plugin
import os
import re
import tempfile
import hashlib
import json
from datetime import datetime

def plugin_loaded():
    """Initialize the plugin when Sublime Text loads."""
    SublimeTeraManager.initialize()

class SublimeTeraManager:
    """Manages Tera syntax files and their generation."""
    
    cache_dir = None
    generated_syntaxes = {}
    cache_file = None
    debug_mode = False
    
    @classmethod
    def initialize(cls):
        """Initialize the syntax manager and create necessary directories."""
        # Set up cache directory
        cls.cache_dir = os.path.join(sublime.cache_path(), "SublimeTera")
        if not os.path.exists(cls.cache_dir):
            os.makedirs(cls.cache_dir)
        
        # Set up cache file for generated syntaxes
        cls.cache_file = os.path.join(cls.cache_dir, "syntax_cache.json")
        
        # Load existing cache if available
        if os.path.exists(cls.cache_file):
            try:
                with open(cls.cache_file, 'r') as f:
                    cls.generated_syntaxes = json.load(f)
            except Exception as e:
                print(f"SublimeTera: Error loading cache file - {e}")
                cls.generated_syntaxes = {}
    
    @classmethod
    def log(cls, message):
        """Log debug messages if debug mode is enabled."""
        if cls.debug_mode:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"SublimeTera [{timestamp}]: {message}")
    
    @classmethod
    def find_base_syntax_for_extension(cls, extension):
        """Find the appropriate base syntax for a given file extension."""
        # Default to HTML if no extension or unknown
        if not extension:
            return "Packages/HTML/HTML.sublime-syntax", "text.html.basic"
        
        # Search all available syntax files
        for syntax_path in sublime.find_resources('*.sublime-syntax'):
            try:
                syntax_content = sublime.load_resource(syntax_path)
                
                # Skip Tera syntax files to avoid recursion
                if "name: Tera" in syntax_content:
                    continue
                
                # Extract file extensions from syntax definition
                extensions_match = re.search(r'file_extensions:(?:\s*-\s*[\w.]+)+', syntax_content, re.DOTALL)
                if not extensions_match:
                    continue
                
                extensions = re.findall(r'-\s*([\w.]+)', extensions_match.group(0))
                if extension in extensions:
                    # Found a matching syntax
                    scope_match = re.search(r'scope:\s*([\w.]+)', syntax_content)
                    scope = scope_match.group(1) if scope_match else f"source.{extension}"
                    
                    return syntax_path, scope
            except Exception as e:
                cls.log(f"Error processing syntax {syntax_path}: {e}")
        
        # Default to HTML if no matching syntax found
        return "Packages/HTML/HTML.sublime-syntax", "text.html.basic"
    
    @classmethod
    def generate_combined_syntax(cls, base_ext, base_path, base_scope):
        """Generate a combined Tera + base language syntax file."""
        # Generate a unique identifier for this syntax
        syntax_id = hashlib.md5(f"{base_path}_{base_scope}".encode()).hexdigest()
        
        # Check if we've already generated this syntax
        if syntax_id in cls.generated_syntaxes:
            syntax_file = cls.generated_syntaxes[syntax_id].get('path')
            if syntax_file and os.path.exists(syntax_file):
                return syntax_file
        
        # Generate a new combined syntax file
        package_name = os.path.basename(os.path.dirname(base_path))
        syntax_name = os.path.basename(base_path).replace('.sublime-syntax', '')
        
        # Create friendly names for the syntax
        if base_ext:
            display_name = f"Tera {base_ext.upper()}"
            file_name = f"Tera{base_ext.capitalize()}.sublime-syntax"
        else:
            display_name = f"Tera {syntax_name}"
            file_name = f"Tera{syntax_name}.sublime-syntax"
        
        # Path for the new syntax file
        syntax_file = os.path.join(cls.cache_dir, file_name)
        
        # Create the syntax content
        syntax_content = f"""
%YAML 1.2
---
# Auto-generated Tera combined syntax - base: {base_path}
name: {display_name}
file_extensions:
  - {base_ext}.tera
scope: {base_scope}.tera
hidden: false

contexts:
  main:
    # Include Tera syntax first so it takes precedence
    - include: 'Packages/SublimeTera/Tera.sublime-syntax#tera_blocks'
    # Include the base language syntax
    - include: scope:{base_scope}
"""
        
        # Write the syntax file
        with open(syntax_file, 'w', encoding='utf-8') as f:
            f.write(syntax_content)
        
        # Update cache
        cls.generated_syntaxes[syntax_id] = {
            'path': syntax_file,
            'base_path': base_path,
            'base_scope': base_scope,
            'created': datetime.now().isoformat()
        }
        
        # Save cache
        try:
            with open(cls.cache_file, 'w') as f:
                json.dump(cls.generated_syntaxes, f, indent=2)
        except Exception as e:
            cls.log(f"Error saving syntax cache: {e}")
        
        return syntax_file

class TeraFiletypeDetector(sublime_plugin.EventListener):
    """Event listener to detect and apply Tera syntax highlighting."""
    
    def on_load_async(self, view):
        self.detect_and_set_syntax(view)
    
    def on_reload_async(self, view):
        self.detect_and_set_syntax(view)
    
    def on_post_save_async(self, view):
        self.detect_and_set_syntax(view)
    
    def detect_and_set_syntax(self, view):
        """Detect the file's base language and apply the appropriate Tera syntax."""
        # Check if this is a .tera file
        filename = view.file_name()
        if not filename or not filename.endswith('.tera'):
            return
        
        # Extract base extension if any
        basename = os.path.basename(filename)
        tera_pos = basename.rfind('.tera')
        if tera_pos == -1:
            return
        
        # Find the last dot before .tera
        dot_pos = basename.rfind('.', 0, tera_pos)
        
        # Determine base extension
        if dot_pos == -1:
            # No dot found, assume it's plain .tera
            base_ext = ""
        else:
            # Extract the extension
            base_ext = basename[dot_pos+1:tera_pos].lower()
        
        # Find the appropriate base syntax for this extension
        base_syntax_path, base_scope = SublimeTeraManager.find_base_syntax_for_extension(base_ext)
        
        # Generate a combined syntax
        syntax_file = SublimeTeraManager.generate_combined_syntax(base_ext, base_syntax_path, base_scope)
        
        # Apply the syntax to the view
        if syntax_file:
            view.assign_syntax(syntax_file)

class TeraToggleDebugModeCommand(sublime_plugin.ApplicationCommand):
    """Toggle debug mode for Tera syntax."""
    
    def run(self):
        SublimeTeraManager.debug_mode = not SublimeTeraManager.debug_mode
        status = "enabled" if SublimeTeraManager.debug_mode else "disabled"
        sublime.status_message(f"Tera Syntax: Debug mode {status}")

class TeraClearSyntaxCacheCommand(sublime_plugin.ApplicationCommand):
    """Clear the syntax cache."""
    
    def run(self):
        # Clear the cache dictionary
        SublimeTeraManager.generated_syntaxes = {}
        
        # Save empty cache
        try:
            with open(SublimeTeraManager.cache_file, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            print(f"SublimeTera: Error clearing cache - {e}")
        
        # Delete all generated syntax files
        for file in os.listdir(SublimeTeraManager.cache_dir):
            if file.endswith('.sublime-syntax'):
                try:
                    os.remove(os.path.join(SublimeTeraManager.cache_dir, file))
                except Exception as e:
                    print(f"SublimeTera: Error removing file {file} - {e}")
        
        sublime.status_message("Tera Syntax: Cache cleared")
