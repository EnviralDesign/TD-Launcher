# Building TD Launcher for Mac OS

This guide explains how to build TD Launcher for Mac OS, creating a standalone app bundle and optional DMG installer.

## 🔧 Prerequisites

### Required:
- **macOS 10.15+** (Catalina or newer)
- **Python 3.8+** installed
- **TouchDesigner** installed (for testing)

### Recommended:
- **Virtual environment** for Python dependencies
- **Homebrew** for optional tools
- **Xcode Command Line Tools**: `xcode-select --install`

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Make scripts executable (if needed)
chmod +x setup_mac.sh BUILD_mac_simple.sh BUILD_mac.sh td_launcher.sh

# Run setup script
./setup_mac.sh
```

### 2. Simple Build (Development)
```bash
# Creates app bundle only
./BUILD_mac_simple.sh
```

### 3. Full Build (Distribution)
```bash
# Creates app bundle + DMG installer
./BUILD_mac.sh
```

## 📂 Build Outputs

After building, you'll find:

```
dist/
├── TD Launcher.app           # Mac app bundle
└── TD_Launcher_Installer.dmg # DMG installer (full build only)
```

## 🧪 Testing

### Test the App Bundle:
```bash
# Launch the app
open "dist/TD Launcher.app"

# Launch with a specific .toe file
open "dist/TD Launcher.app" --args /path/to/your/project.toe
```

### Test Before Building:
```bash
# Run directly from source
./td_launcher.sh

# Or with Python
python3 td_launcher.py
```

## 📋 Manual Build Steps

If you prefer manual control:

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Run PyInstaller
```bash
pyinstaller --noconfirm --log-level=WARN \
    --onefile \
    --windowed \
    --name="TD Launcher" \
    --icon="td_launcher.ico" \
    --add-data="test.toe:." \
    --osx-bundle-identifier="com.enviral-design.td-launcher" \
    --target-arch=universal2 \
    td_launcher.py
```

### 3. Create DMG (Optional)
```bash
# Install create-dmg if needed
brew install create-dmg

# Create DMG
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
```

## 🔍 Build Scripts Explained

### `setup_mac.sh`
- Checks Python installation
- Installs Python dependencies
- Makes scripts executable
- Checks for optional tools
- Tests basic functionality

### `BUILD_mac_simple.sh`
- Quick build for development
- Creates app bundle only
- Auto-installs missing dependencies
- Good for testing changes

### `BUILD_mac.sh` 
- Full production build
- Creates app bundle + DMG
- Universal binary support
- Includes proper bundle identifier

## 🏗️ Build Architecture Support

The build creates **Universal** binaries that work on:
- ✅ **Intel Macs** (x86_64)
- ✅ **Apple Silicon Macs** (M1/M2/M3)

This is achieved with `--target-arch=universal2` in PyInstaller.

## 🐛 Troubleshooting

### "pyinstaller not found"
```bash
pip3 install pyinstaller
```

### "dearpygui import error"
```bash
pip3 install dearpygui
```

### Permission denied on scripts
```bash
chmod +x *.sh
```

### DMG creation fails
```bash
# Install create-dmg
brew install create-dmg

# Or skip DMG creation - app bundle works fine
```

### Universal binary issues
Remove `--target-arch=universal2` to build for current architecture only.

## 📦 Distribution

### For Users:
- Distribute the **DMG file** for easy installation
- Users drag the app to Applications folder

### For Developers:
- The **app bundle** can be run directly
- No installation required

## 🔐 Code Signing (Optional)

For distribution outside the App Store:

```bash
# Sign the app (requires Apple Developer account)
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/TD Launcher.app"

# Notarize (requires Apple Developer account)
xcrun notarytool submit "dist/TD_Launcher_Installer.dmg" --keychain-profile "notarytool-profile" --wait
```

## 🆚 Windows vs Mac Build Differences

| Aspect | Windows (BUILD.bat) | Mac (BUILD_mac.sh) |
|--------|--------------------|--------------------|
| **Bundled Files** | toeexpand.exe + DLLs | test.toe only |
| **Output** | Single .exe | .app bundle |
| **Installer** | Inno Setup .exe | DMG file |
| **Dependencies** | Bundled Python env | System Python |
| **Architecture** | x64 only | Universal (Intel + ARM) |

The Mac version is cleaner because:
- No need to bundle toeexpand (uses TD's copy)
- No DLL dependencies
- macOS handles app bundles natively