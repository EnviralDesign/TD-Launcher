#!/bin/bash
# Mac setup script for TD Launcher development
# Installs Python dependencies and prepares build environment

set -e

echo "Setting up TD Launcher development environment for Mac..."
echo "=" * 60

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Found: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3.8+ from python.org"
    exit 1
fi

# Check if we're in a virtual environment (recommended)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected."
    echo "   Consider creating one with: python3 -m venv td_launcher_env"
    echo "   Then activate it with: source td_launcher_env/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Make build scripts executable
echo ""
echo "Making build scripts executable..."
chmod +x BUILD_mac.sh
chmod +x BUILD_mac_simple.sh
chmod +x td_launcher.sh

# Check for optional tools
echo ""
echo "Checking optional tools..."

if command -v create-dmg &> /dev/null; then
    echo "✅ create-dmg found (DMG creation available)"
else
    echo "⚠️  create-dmg not found (optional for DMG creation)"
    echo "   Install with: brew install create-dmg"
fi

if command -v brew &> /dev/null; then
    echo "✅ Homebrew found"
else
    echo "⚠️  Homebrew not found (recommended for Mac development)"
    echo "   Install from: https://brew.sh"
fi

# Test the basic functionality
echo ""
echo "Testing basic functionality..."
if python3 -c "import dearpygui, platform, plistlib, glob; print('✅ All imports successful')" 2>/dev/null; then
    echo "✅ All Python dependencies working"
else
    echo "❌ Some Python dependencies failed to import"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test the launcher: ./td_launcher.sh"
echo "2. Build the app: ./BUILD_mac_simple.sh"
echo "3. For distribution: ./BUILD_mac.sh"
echo ""
echo "Happy coding! 🚀"