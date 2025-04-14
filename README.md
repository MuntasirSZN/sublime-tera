# Tera Syntax for Sublime Text

A simple syntax highlighting package for Tera templates in Sublime Text.

## Features

- Syntax highlighting for Tera templates (`.tera` files)
- HTML syntax highlighting for template content
- Support for all Tera template constructs:
  - Comments `{# ... #}`
  - Expressions `{{ ... }}`
  - Statements `{% ... %}`
  - Blocks, conditionals, loops, etc.

## Installation

### Manual Installation

1. Download or clone this repository
2. Go to `Preferences > Browse Packages...` in Sublime Text
3. Copy the `TeraSyntax` folder into the Packages directory
4. Restart Sublime Text

### Package Control (Coming Soon)

Once this package is available in Package Control, you'll be able to install it by:

1. Opening the command palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Selecting `Package Control: Install Package`
3. Searching for `Tera Syntax` and pressing Enter

## Usage

Files with `.tera` extension will automatically use this syntax.

## License

MIT License

## Thanks To

@uncenter for [vscode-tera](https://github.com/uncenter/vscode-tera). This repo is a port of vscode's tmLanguage.
