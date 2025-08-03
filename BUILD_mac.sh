#!/bin/bash
# Mac build script for TD Launcher
# Creates a standalone Mac app bundle

set -e  # Exit on any error

echo "Building TD Launcher for Mac..."

# Check if pyinstaller is available
if ! command -v pyinstaller &> /dev/null; then
    echo "Error: pyinstaller not found. Install with: pip3 install pyinstaller"
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/

# Build the app bundle
echo "Running PyInstaller..."
pyinstaller --noconfirm --log-level=WARN \
    --onefile \
    --windowed \
    --name="TD Launcher" \
    --icon="td_launcher.ico" \
    --add-data="test.toe:." \
    --osx-bundle-identifier="com.enviral-design.td-launcher" \
    --target-arch=universal2 \
    td_launcher.py

echo "Build completed!"
echo "App bundle created at: dist/TD Launcher.app"

# Optional: Create a DMG (requires create-dmg or similar tool)
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG installer..."
    create-dmg \
        --volname "TD Launcher Installer" \
        --volicon "td_launcher.ico" \
        --window-pos 200 120 \
        --window-size 600 300 \
        --icon-size 100 \
        --icon "TD Launcher.app" 175 120 \
        --hide-extension "TD Launcher.app" \
        --app-drop-link 425 120 \
        "dist/TD_Launcher_Installer.dmg" \
        "dist/"
    echo "DMG created at: dist/TD_Launcher_Installer.dmg"
else
    echo "Note: install 'create-dmg' for DMG creation: brew install create-dmg"
fi

echo ""
echo "Build Summary:"
echo "=============="
echo "App Bundle: dist/TD Launcher.app"
if [ -f "dist/TD_Launcher_Installer.dmg" ]; then
    echo "DMG Installer: dist/TD_Launcher_Installer.dmg"
fi
echo ""
echo "To test the app:"
echo "  open 'dist/TD Launcher.app'"
echo "  or"
echo "  open 'dist/TD Launcher.app' --args /path/to/test.toe"