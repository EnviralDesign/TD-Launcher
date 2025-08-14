#!/bin/bash
# Simple Mac build script - creates app bundle without DMG
# Optimized for Apple Silicon (arm64) - Good for development and testing

set -e

echo "Building TD Launcher (Mac - Simple)..."

# Check dependencies
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing pyinstaller..."
    pip3 install pyinstaller
fi

if ! python3 -c "import dearpygui" 2>/dev/null; then
    echo "Installing dearpygui..."
    pip3 install dearpygui
fi

# Clean and build
echo "Cleaning previous builds..."
rm -rf build/ dist/

echo "Building app bundle..."
pyinstaller --noconfirm --log-level=WARN "TD Launcher.spec"

echo ""
echo "✅ Build completed!"
echo "📱 App bundle: dist/TD Launcher.app"
echo ""
echo "🧪 To test:"
echo "   open 'dist/TD Launcher.app'"