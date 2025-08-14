# TD_Launcher
A standalone launcher application for automatically opening TouchDesigner projects (.toe files) with the correct version.

### Toe autolaunch
![image](https://user-images.githubusercontent.com/10091486/185008821-c4294500-7e1b-47d2-b3df-881519591de5.png)

### Download TD and Install from Launcher
![image](https://user-images.githubusercontent.com/10091486/185009037-6569848a-dd25-4766-a73e-23a770b5e36b.png)
![image](https://user-images.githubusercontent.com/10091486/185009082-c09f20f5-01b6-4d8e-9a42-9e820844a9ec.png)
![image](https://user-images.githubusercontent.com/10091486/185009223-7d1f5840-02cb-4eae-b6b8-a26d4c8e032a.png)

### Older Builds not yet supported
![image](https://user-images.githubusercontent.com/10091486/185009295-71c275b8-c295-44d5-ac47-98c514e2f115.png)



## What's this for


If you work on a lot of TD projects, or support many older projects you know the pain of having to manage / guess / remember which version something was built in. A real pain if you accidentally upgrade your projects build and lose work when trying to downgrade back again!

## How this works
This tool scans your computer when launched for TouchDesigner entries, and builds a list of available TD executable paths that can potentially be used. It then analyzes the .toe file and loads the GUI with the appropriate option selected, and starts a 5 second timer.

If you interupt it by clicking anywhere, you can choose a different version or cancel. If you leave it undisturbed, it will launch after 5 sec in the detected version.

If the required version of Touch is not found, the launcher will not launch anything automatically, and will wait for your input with the required build highlighted in red.

## How to use

### Windows
1. Download the installer from the releases page on the right
2. Run the installer to install TD Launcher
3. Set Windows to open `.toe` files with TD Launcher by default
4. Double-clicking `.toe` files will now launch them with TD Launcher

### macOS
1. Download the `.dmg` file from the releases page
2. Open the DMG and drag "TD Launcher" to the "Applications" folder
3. **File association is automatic!** TD Launcher will appear as an option for `.toe` files
4. **Optional:** To make it the default, right-click any `.toe` file → "Get Info" → set "Open with" to "TD Launcher" → "Change All..."
5. Double-clicking `.toe` files will now launch them with TD Launcher

### Alternative Usage
You can also drag and drop `.toe` files directly onto the TD Launcher app icon.

## How to build
This was built with Python 3.10. Pyinstaller, and the wonderful [DearPyGui](https://github.com/hoffstadt/DearPyGui) for UI amongst other things.

By default, Pyinstaller compiled programs when downloaded directly from the internet as an exe or zipped exe tend to get flagged as false positive viruses, for this one it showed up as Trojan:Win32/Wacatac.B!ml, which is of course nonsense. 

To get around this for those downloading releases, I bundled the executable into a windows installer using inno setup which conveniently compresses the contents into a format chrome, windows etc can't read at download time.

If you want to build from this repo, there's a few steps, but they are mostly automated.

1) download this repo
2) unzip the py directory from inside py.zip into the root of the repo. This is a full python install, with Pyinstaller DearPyGui, etc installed.
3) make your changes to td_launcher.py, the main script.
4) test td_launcher.py easily by just double clicking td_launcher.bat. (NOTE: when doubleclicking to run, it uses a bundled test.toe as a test file for simplicity.)
5) when ready to rebuild the single file exe with pyinstaller, run BUILD.bat. This will create the executable in dist\td_launcher.exe.
6) optionally if you also wish to bundle the exe into an installer, you can open the iss file inno\TD_Launcher_Inno_Compiler.iss, with [inno setup](https://jrsoftware.org/isinfo.php), and build from there. separate installer.exe will show up in the inno\Output\ directory.

### macOS Build

The macOS build is optimized for Apple Silicon (M1/M2/M3/etc) Macs and includes file association support for `.toe` files.

#### Prerequisites
1. **TouchDesigner installed** - Required for `toeexpand` utility
2. **Python 3.9+** with pip
3. **Xcode Command Line Tools**: `xcode-select --install`

#### Quick Setup
```bash
# 1. Clone the repository
git clone <repo-url>
cd TD-Launcher-Mac

# 2. Set up Python virtual environment
./setup_mac.sh

# 3. Build the app (simple version for development)
./BUILD_mac_simple.sh

# 4. Build creates automatic file association support
```

#### Build Options

**Development Build (Recommended):**
```bash
./BUILD_mac_simple.sh
```
- Quick build for testing
- Creates `dist/TD Launcher.app`
- Includes debug logging support

**Distribution Build:**
```bash
./BUILD_mac.sh
```
- Full build with DMG creation
- Requires `brew install create-dmg` for DMG generation
- Creates both app bundle and installer DMG

#### Testing & Debugging

**Test the built app:**
```bash
# Test built app bundle with debug logging
export TD_LAUNCHER_DEBUG=1
open "dist/TD Launcher.app" --args test.toe


```

**Run from source with debugging:**
```bash
# Enable debug logging
export TD_LAUNCHER_DEBUG=1
python3 td_launcher.py test.toe
```

#### File Association Setup

The built app automatically includes file association support for `.toe` files. After building:

1. **Install the app:**
   - Copy `dist/TD Launcher.app` to `/Applications/`
   - Or install via the DMG (distribution build)

2. **Set as default (if needed):**
   - Right-click any `.toe` file
   - Select "Get Info"
   - In "Open with" section, select "TD Launcher"
   - Click "Change All..." to set as default

**Note:** File associations activate automatically when the app is in `/Applications/`. No manual registration required.

#### Build Requirements

The build process requires these Python packages (automatically installed by `setup_mac.sh`):
- `dearpygui>=1.9.0` - GUI framework
- `pyinstaller>=5.0` - App bundling
- `Pillow>=9.0.0` - Icon processing

#### Architecture Notes

- **Apple Silicon**: Native ARM64 build for optimal performance
- **Intel Macs**: Can run via Rosetta 2 translation
- **Universal Binary**: Not supported due to dearpygui limitations

#### Troubleshooting


**TouchDesigner not detected:**
- Ensure TouchDesigner is installed in `/Applications/`
- Check that `toeexpand` exists in TouchDesigner.app bundle

**File association not working:**
- Ensure app is installed in `/Applications/`
- Try: Right-click `.toe` file → "Open With" → "TD Launcher"
- Restart Finder: `killall Finder`
- Enable debug logging: `export TD_LAUNCHER_DEBUG=1` and check `~/Desktop/td_launcher_debug.log`

---

## Developer Notes

### Platform-Specific TOE File Analysis

TD Launcher uses TouchDesigner's `toeexpand` utility to analyze `.toe` files and determine the required TouchDesigner version. The implementation differs between platforms:

#### Windows
- **Bundled approach**: Uses the `toeexpand.exe` included in the `toeexpand/` directory
- **Self-contained**: No dependency on installed TouchDesigner versions
- **Consistent**: Always uses the same `toeexpand` version regardless of system state

#### macOS
- **Dynamic discovery**: Searches for `toeexpand` within installed TouchDesigner applications
- **Location**: `TouchDesigner.app/Contents/MacOS/toeexpand`
- **Requirement**: At least one TouchDesigner installation must be present on the system
- **Fallback**: Uses the first available TouchDesigner installation found in `/Applications/`

#### Technical Details
```bash
# macOS: Dynamic path resolution
/Applications/TouchDesigner.2023.11600.app/Contents/MacOS/toeexpand -b file.toe

# Windows: Bundled utility
./toeexpand/toeexpand.exe -b file.toe
```

This approach ensures optimal compatibility on each platform while maintaining the core functionality of version detection.

---

If you have any issues, please post a bug issue here.
