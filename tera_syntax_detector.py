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
    TeraSyntaxManager.initialize()
    
    # Print debug info
    print("=======================================")
    print("Tera Syntax Package loaded successfully")
    print("Commands available:")
    print("  - tera_toggle_debug_mode")
    print("  - tera_clear_syntax_cache")
    print("  - tera_reload_syntax")
    print("  - tera_set_syntax")
    print("=======================================")

class TeraSyntaxManager:
    """Manages Tera syntax files and their generation."""
    
    cache_dir = None
    generated_syntaxes = {}
    cache_file = None
    debug_mode = True  # Set to True for debugging
    
    @classmethod
    def initialize(cls):
        """Initialize the syntax manager and create necessary directories."""
        # Set up cache directory
        cls.cache_dir = os.path.join(sublime.cache_path(), "TeraSyntax")
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
                print(f"TeraSyntax: Error loading cache file - {e}")
                cls.generated_syntaxes = {}
    
    @classmethod
    def log(cls, message):
        """Log debug messages if debug mode is enabled."""
        if cls.debug_mode:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"TeraSyntax [{timestamp}]: {message}")
    
    @classmethod
    def find_base_syntax_for_extension(cls, extension):
        """Find the appropriate base syntax for a given file extension."""
        # Default to HTML if no extension or unknown
        if not extension:
            return "Packages/HTML/HTML.sublime-syntax", "text.html.basic"
        
        cls.log(f"Looking for syntax matching extension: {extension}")
        
        # Search all available syntax files
        for syntax_path in sublime.find_resources('*.sublime-syntax'):
            try:
                # Skip our own Tera syntax files
                if "TeraSyntax" in syntax_path and "Tera" in os.path.basename(syntax_path):
                    continue
                
                syntax_content = sublime.load_resource(syntax_path)
                
                # Extract file extensions from syntax definition
                extensions_match = re.search(r'file_extensions:(?:\s*-\s*[\w.]+)+', syntax_content, re.DOTALL)
                if not extensions_match:
                    continue
                
                extensions = re.findall(r'-\s*([\w.]+)', extensions_match.group(0))
                cls.log(f"  Checking {syntax_path}: extensions = {extensions}")
                
                if extension in extensions:
                    # Found a matching syntax
                    scope_match = re.search(r'scope:\s*([\w.]+)', syntax_content)
                    scope = scope_match.group(1) if scope_match else f"source.{extension}"
                    
                    cls.log(f"  Found matching syntax: {syntax_path} with scope {scope}")
                    return syntax_path, scope
            except Exception as e:
                cls.log(f"Error processing syntax {syntax_path}: {e}")
        
        # Default to HTML if no matching syntax found
        cls.log(f"No matching syntax found for {extension}, defaulting to HTML")
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
                cls.log(f"Using cached syntax file: {syntax_file}")
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

variables:
  identifier: '[a-zA-Z_][a-zA-Z0-9_]*'

contexts:
  # The main context first checks for Tera template elements, then falls back to the base language
  main:
    # Comments
    - match: '{#-?'
      captures:
        0: punctuation.definition.comment.begin.tera
      push:
        - meta_scope: comment.block.tera
        - match: '-?#}'
          captures:
            0: punctuation.definition.comment.end.tera
          pop: true
    
    # Expression tags {{ ... }}
    - match: '({{)-?'
      captures:
        0: punctuation.definition.template.begin.tera
      push:
        - meta_scope: meta.template.expression.tera
        - match: '-?(}})'
          captures:
            0: punctuation.definition.template.end.tera
          pop: true
        - include: expression
    
    # Statement tags {% ... %}
    - match: '({%)-?\\s*(if|elif|for|filter|macro|set|set_global|include|import|extends)\\s+'
      captures:
        0: punctuation.definition.template.begin.tera
        1: punctuation.definition.template.begin.tera
        2: keyword.control.tera
      push:
        - meta_scope: meta.template.statement.tera
        - match: '-?(%})'
          captures:
            0: punctuation.definition.template.end.tera
          pop: true
        - include: expression
        
    # Block tags
    - match: '({%)-?\\s*(block|endblock|filter|endfilter|endmacro)\\s+'
      captures:
        0: punctuation.definition.template.begin.tera
        1: punctuation.definition.template.begin.tera
        2: keyword.control.tera
      push:
        - meta_scope: meta.template.block.tera
        - match: '-?(%})'
          captures:
            0: punctuation.definition.template.end.tera
          pop: true
        - include: expression
    
    # Control tags
    - match: '({%)-?\\s*(else|elif|endif|endfor|continue|break|endblock|endfilter|endmacro)\\s*'
      captures:
        0: punctuation.definition.template.begin.tera
        1: punctuation.definition.template.begin.tera
        2: keyword.control.tera
      push:
        - meta_scope: meta.template.control.tera
        - match: '-?(%})'
          captures:
            0: punctuation.definition.template.end.tera
          pop: true
    
    # Raw content tags
    - match: '({%)-?\\s*(raw)\\s*(%})'
      captures:
        0: punctuation.definition.template.begin.tera
        1: punctuation.definition.template.begin.tera
        2: keyword.control.tera
        3: punctuation.definition.template.end.tera
      push:
        - meta_scope: meta.template.raw.tera
        - match: '({%)-?\\s*(endraw)\\s*(%})'
          captures:
            0: punctuation.definition.template.end.tera
            1: punctuation.definition.template.begin.tera
            2: keyword.control.tera
            3: punctuation.definition.template.end.tera
          pop: true
    
    # Default to base language for non-Tera content
    - include: scope:{base_scope}

  # Expression context for inside template tags
  expression:
    # Variables and identifiers
    - match: '(\\.)([a-zA-Z_][a-zA-Z0-9_]*)'
      captures:
        1: punctuation.accessor.tera
        2: entity.name.property.tera
    
    - match: '\\b{{identifier}}\\b'
      scope: variable.other.tera
    
    # Literals
    - match: '"'
      scope: punctuation.definition.string.begin.tera
      push:
        - meta_scope: string.quoted.double.tera
        - match: '"'
          scope: punctuation.definition.string.end.tera
          pop: true
    
    - match: "'"
      scope: punctuation.definition.string.begin.tera
      push:
        - meta_scope: string.quoted.single.tera
        - match: "'"
          scope: punctuation.definition.string.end.tera
          pop: true
    
    - match: '\\b[0-9]+(\.[0-9]+)?\\b'
      scope: constant.numeric.tera
    
    - match: '\\b(true|false)\\b'
      scope: constant.language.boolean.tera
    
    # Operators
    - match: '(\\+|\\-|\\*|/|%|~)'
      scope: keyword.operator.arithmetic.tera
    
    - match: '(==|>=|<=|<|>|!=)'
      scope: keyword.operator.comparison.tera
    
    - match: '='
      scope: keyword.operator.assignment.tera
    
    - match: '\\b(in|and|or|not|is|as)\\b'
      scope: keyword.operator.logical.tera
    
    # Filters
    - match: '(\\|)\\s*\\b([a-zA-Z_][a-zA-Z0-9_]*)\\b'
      captures:
        1: keyword.operator.filter.tera
        2: support.function.filter.tera
"""
        
        # Write the syntax file
        cls.log(f"Creating new syntax file: {syntax_file}")
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
        
        TeraSyntaxManager.log(f"Detected file {filename} with base extension: {base_ext}")
        
        # Find the appropriate base syntax for this extension
        base_syntax_path, base_scope = TeraSyntaxManager.find_base_syntax_for_extension(base_ext)
        
        # Generate a combined syntax
        syntax_file = TeraSyntaxManager.generate_combined_syntax(base_ext, base_syntax_path, base_scope)
        
        # Apply the syntax to the view
        if syntax_file:
            TeraSyntaxManager.log(f"Applying syntax {syntax_file} to view")
            view.assign_syntax(syntax_file)
            sublime.status_message(f"Tera: Using {os.path.basename(syntax_file)} syntax")

class TeraToggleDebugModeCommand(sublime_plugin.ApplicationCommand):
    """Toggle debug mode for Tera syntax."""
    
    def run(self):
        TeraSyntaxManager.debug_mode = not TeraSyntaxManager.debug_mode
        status = "enabled" if TeraSyntaxManager.debug_mode else "disabled"
        sublime.status_message(f"Tera Syntax: Debug mode {status}")

class TeraClearSyntaxCacheCommand(sublime_plugin.ApplicationCommand):
    """Clear the syntax cache."""
    
    def run(self):
        # Clear the cache dictionary
        TeraSyntaxManager.generated_syntaxes = {}
        
        # Save empty cache
        try:
            with open(TeraSyntaxManager.cache_file, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            print(f"TeraSyntax: Error clearing cache - {e}")
        
        # Delete all generated syntax files
        for file in os.listdir(TeraSyntaxManager.cache_dir):
            if file.endswith('.sublime-syntax'):
                try:
                    os.remove(os.path.join(TeraSyntaxManager.cache_dir, file))
                except Exception as e:
                    print(f"TeraSyntax: Error removing file {file} - {e}")
        
        sublime.status_message("Tera Syntax: Cache cleared")

class TeraReloadSyntaxCommand(sublime_plugin.TextCommand):
    """Reload the Tera syntax for the current file."""
    
    def run(self, edit):
        view = self.view
        filename = view.file_name()
        
        if not filename or not filename.endswith('.tera'):
            sublime.status_message("Not a Tera template file")
            return
        
        # Get the detector and force reload
        detector = TeraFiletypeDetector()
        detector.detect_and_set_syntax(view)
        
        # Clear the cache first
        sublime.run_command("tera_clear_syntax_cache")
        sublime.status_message("Tera syntax reloaded")

class TeraSetSyntaxCommand(sublime_plugin.TextCommand):
    """Set the current file as a Tera template."""
    
    def run(self, edit):
        view = self.view
        filename = view.file_name()
        
        if not filename:
            sublime.status_message("File must be saved first")
            return
        
        # Get the current syntax
        current_syntax = view.syntax()
        if not current_syntax:
            # Default to HTML
            base_scope = "text.html.basic"
            base_path = "Packages/HTML/HTML.sublime-syntax"
        else:
            base_scope = current_syntax.scope
            base_path = current_syntax.path
        
        # Generate an appropriate extension
        base_ext = self._scope_to_extension(base_scope)
        
        # Generate a combined syntax
        syntax_file = TeraSyntaxManager.generate_combined_syntax(base_ext, base_path, base_scope)
        
        # Apply the syntax to the view
        if syntax_file:
            view.assign_syntax(syntax_file)
            sublime.status_message(f"Applied Tera {base_ext.upper()} syntax")
    
    def _scope_to_extension(self, scope):
        """Convert a scope to a file extension."""
        scope_map = {
            "text.html.basic": "html",
            "source.json": "json",
            "source.css": "css",
            "source.js": "js",
            "source.python": "py",
            "source.toml": "toml",
            "source.yaml": "yaml",
            "text.html.markdown": "md",
            # Add more mappings as needed
        }
        
        # Extract the base scope (first parts)
        base_scope = '.'.join(scope.split('.')[:2])
        
        return scope_map.get(base_scope, "html")  # Default to html
