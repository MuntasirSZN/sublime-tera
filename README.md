# Sublime Tera Syntax

A Sublime Text package for Tera template syntax highlighting with automatic detection of underlying file types.

## Features

- Syntax highlighting for Tera templates (`.tera` files)
- Automatic detection of base language based on file extension (e.g., `file.html.tera` uses HTML+Tera syntax)
- Support for nested variable properties (like `.hex` in `{{variable.hex}}`)
- Highlights Tera expressions, tags, and comments

## How It Works

The package includes:

1. A base Tera syntax definition for highlighting template tags and expressions
2. A dynamic syntax detector that:
   - Analyzes your file name to determine the underlying language
   - Automatically generates combined syntax definitions
   - Applies the correct highlighting

## Examples

- `page.html.tera` → HTML + Tera highlighting
- `config.toml.tera` → TOML + Tera highlighting
- `style.css.tera` → CSS + Tera highlighting
- `data.json.tera` → JSON + Tera highlighting

If no base extension is detected, HTML highlighting is used as the default.

## Commands

- **Toggle Debug Mode**: Enables logging for troubleshooting
- **Clear Syntax Cache**: Clears cached syntax definitions

## Installation

### Package Control

1. Make sure you have [Package Control](https://packagecontrol.io/) installed
2. Open the command palette (Ctrl+Shift+P / Cmd+Shift+P)
3. Select `Package Control: Add Repository`
4. Paste `https://github.com/MuntasirSZN/sublime-tera`

### Manual Installation

1. Download or clone this repository
2. Go to `Preferences > Browse Packages...` in Sublime Text
3. Copy the `SublimeTera` folder into the Packages directory
4. Restart Sublime Text

## License

MIT License

## Thanks To

@uncenter for [vscode-tera](https://github.com/uncenter/vscode-tera). This repo is a port of vscode's tmLanguage.
