#!/bin/bash

# Simple installation script for PM CLI

echo "Installing PM - Project Management CLI..."

# Install dependencies
pip3 install -r requirements.txt

# Make executable
chmod +x pm.py

# Get the current directory
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "Installation complete!"
echo ""
echo "To use PM from anywhere, add this alias to your ~/.zshrc or ~/.bashrc:"
echo ""
echo "  alias pm='python3 $INSTALL_DIR/pm.py'"
echo ""
echo "Then run: source ~/.zshrc (or ~/.bashrc)"
echo ""
echo "Or use directly: python3 $INSTALL_DIR/pm.py"
