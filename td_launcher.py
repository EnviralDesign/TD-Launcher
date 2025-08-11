import dearpygui.dearpygui as dpg
import subprocess
import os
from pathlib import Path
import shutil
import sys
import time
import urllib.request
import platform
import plistlib
import glob
import logging

# Platform-specific imports
if platform.system() == 'Windows':
    import winreg

app_version = '1.1.0'

# Setup debug logging
# Check if running as app bundle (different working directory patterns)
is_app_bundle = '/Contents/MacOS' in os.path.abspath(__file__) or os.getcwd() == '/'
DEBUG_MODE = os.environ.get('TD_LAUNCHER_DEBUG', '').lower() in ('1', 'true', 'yes')

if DEBUG_MODE:
    # For app bundles, write log to a location we can access
    log_file = os.path.expanduser('~/Desktop/td_launcher_debug.log') if is_app_bundle else 'td_launcher_debug.log'
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    print(f"🐛 DEBUG MODE ENABLED - Logging to console and {log_file}")
    if is_app_bundle:
        print(f"📱 Running as app bundle - debug log: {log_file}")
else:
    logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)

# Debug output only when explicitly enabled
if DEBUG_MODE:
    print("=" * 60)
    print("🐛 TD LAUNCHER DEBUG MODE")
    print("=" * 60)
    print(f"Script file: {__file__}")
    print(f"Absolute script path: {os.path.abspath(__file__)}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Command line args: {sys.argv}")
    print(f"App bundle: {is_app_bundle}")
    print(f"Log file location: {log_file}")
    print("=" * 60)

num_sec_until_autostart = 5
current_directory = os.path.dirname(__file__)
countdown_enabled = True
download_progress = 0.0
should_exit = False  # Global flag for graceful shutdown on macOS

# Essential startup logging only
logger.info(f"TD Launcher v{app_version} starting...")
if DEBUG_MODE:
    logger.debug(f"Command line args: {sys.argv}")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"Platform: {platform.system()} {platform.release()}")

if len(sys.argv) >= 2:
    td_file_path = sys.argv[1] # this gets passed in as argument
    if DEBUG_MODE:
        logger.debug(f"File path from command line: {td_file_path}")
    
    # Convert to absolute path to avoid working directory issues
    if not os.path.isabs(td_file_path):
        td_file_path = os.path.abspath(td_file_path)
        if DEBUG_MODE:
            logger.debug(f"Converted to absolute path: {td_file_path}")
else:
    # No command line argument - this is the file association issue
    if is_app_bundle:
        logger.error("❌ CRITICAL: Running as app bundle but no file argument provided")
        logger.error("This indicates macOS file association is not working correctly")
        logger.error("macOS should pass the file path when launching via file association")
        
        # Show an error dialog to the user
        print("❌ ERROR: No file was passed to TD Launcher")
        print("This usually means the file association is not working correctly.")
        print("")
        print("SOLUTIONS:")
        print("1. Right-click the .toe file → 'Open With' → 'TD Launcher'")
        print("2. Drag and drop the .toe file onto TD Launcher")
        print("3. Run from command line: open 'TD Launcher.app' --args /path/to/file.toe")
        
        # Use bundled test file as absolute fallback
        td_file_path = os.path.join(current_directory, 'test.toe')
        logger.warning(f"Using bundled test file as fallback: {td_file_path}")
    else:
        td_file_path = os.path.join(current_directory, 'test.toe')
        if DEBUG_MODE:
            logger.debug(f"Using default test file: {td_file_path}")

# Validate the file path
if not os.path.exists(td_file_path):
    logger.error(f"File does not exist: {td_file_path}")
    logger.error(f"Directory contents of parent: {os.listdir(os.path.dirname(td_file_path)) if os.path.exists(os.path.dirname(td_file_path)) else 'Parent directory does not exist'}")
    print(f"❌ Error: File not found: {td_file_path}")
else:
    if DEBUG_MODE:
        logger.debug(f"Target file exists: {td_file_path} (size: {os.path.getsize(td_file_path)} bytes)")

def query_td_registry_entries():
    # scan the registry and store any keys we find along the way that contain the string "TouchDesigner"
    reg = winreg.ConnectRegistry(None,winreg.HKEY_CLASSES_ROOT)
    td_matching_keys = []
    for i in range(16384): # just iterate on a really big number.. we exit early if we get to the end anyways.
        try:
            key_name = winreg.EnumKey(reg, i)
        except OSError as e:
            if "WinError 259" in str(e):
                print('reached end of registry, finishing registry scan...')
            else:
                print('unknown OSError', e)
            break

        # if touchdesigner exists in key and if there is no suffix like .Asset or .Component, we save the key.
        if "TouchDesigner" in key_name and key_name.count('.') == 2:
            td_matching_keys += [ key_name ]
    
    td_matching_keys = sorted(td_matching_keys)

    td_key_id_dict = { k:{} for k in td_matching_keys }
    for k,v in td_key_id_dict.items():
        entry_val = winreg.QueryValue(reg, f'{k}\\shell\\open\\command')
        td_key_id_dict[k]['executable'] = entry_val.split('"')[1]
    
    return td_key_id_dict

def query_td_mac_applications():
    """Mac version: scan /Applications for TouchDesigner apps and extract version info from Info.plist"""
    if DEBUG_MODE:
        logger.debug("Scanning for TouchDesigner applications...")
    td_matching_apps = []
    applications_dir = "/Applications"
    
    # Look for TouchDesigner applications
    td_pattern = os.path.join(applications_dir, "TouchDesigner*")
    logger.debug(f"Searching pattern: {td_pattern}")
    td_apps = glob.glob(td_pattern)
    if DEBUG_MODE:
        logger.debug(f"Found {len(td_apps)} potential TouchDesigner apps")
    
    td_key_id_dict = {}
    
    for app_path in td_apps:
        if not app_path.endswith('.app'):
            continue
            
        app_name = os.path.basename(app_path)
        info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
        logger.debug(f"Processing app: {app_name}")
        logger.debug(f"Info.plist path: {info_plist_path}")
        
        try:
            # Read the Info.plist file
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            # Extract version information
            bundle_version = plist_data.get('CFBundleVersion', '')
            bundle_name = plist_data.get('CFBundleName', app_name)
            logger.debug(f"Bundle version: {bundle_version}, Bundle name: {bundle_name}")
            
            if bundle_version:
                # Create a key in the format TouchDesigner.VERSION.BUILD
                # Parse the version to match Windows registry format
                version_parts = bundle_version.split('.')
                if len(version_parts) >= 2:
                    year = version_parts[0]
                    build = version_parts[1] if len(version_parts) > 1 else "0"
                    td_key = f"TouchDesigner.{year}.{build}"
                    
                    # Path to the executable inside the app bundle
                    executable_path = os.path.join(app_path, "Contents", "MacOS", "TouchDesigner")
                    
                    td_key_id_dict[td_key] = {
                        'executable': executable_path,
                        'app_path': app_path,
                        'bundle_version': bundle_version
                    }
                    if DEBUG_MODE:
                        logger.debug(f"Found TouchDesigner: {td_key} at {executable_path}")
                else:
                    logger.warning(f"Could not parse version from {bundle_version}")
            else:
                logger.warning(f"No bundle version found for {app_name}")
                    
        except (FileNotFoundError, plistlib.InvalidFileException, KeyError) as e:
            logger.error(f"Could not read Info.plist for {app_path}: {e}")
            print(f"Could not read Info.plist for {app_path}: {e}")
            continue
    
    return td_key_id_dict

'''
def inspect_toe():
    # This function is no longer used, but keeping for reference. Since newer versions of toeexpand do not require dumping the .build directory
    # to disk, we can simply get the build option from the subprocess output as seen in the _v2 function below.

    td_file_path_osstyle = td_file_path.replace('/','\\')
    command = f'"{current_directory}\\toeexpand\\toeexpand.exe" "{td_file_path_osstyle}" .build'

    expand_dir = f'{td_file_path_osstyle}.dir'
    expand_toc = f'{td_file_path_osstyle}.toc'

    expand_dir_obj = Path(expand_dir)
    if expand_dir_obj.exists() == True:
        shutil.rmtree(expand_dir_obj.resolve())

    expand_toc_obj = Path(expand_toc)
    if expand_toc_obj.exists() == True:
        os.remove(expand_toc_obj.resolve())

    res = subprocess.call(command, shell = True)
    build_file = f'{expand_dir}\\.build'
    
    with open(build_file,'r',encoding = 'utf-8') as f:
        build_info = f.read()
    
    expand_dir_obj = Path(expand_dir)
    if expand_dir_obj.exists() == True:
        shutil.rmtree(expand_dir_obj.resolve())

    expand_toc_obj = Path(expand_toc)
    if expand_toc_obj.exists() == True:
        os.remove(expand_toc_obj.resolve())
    
    info_split = build_info.split('\n')
    # print(info_split)
    build_option = f'TouchDesigner.{info_split[1].split(" ")[-1]}'
    
    return build_option
'''

def inspect_toe_v2():
    # this version of inspect_toe does not need to access extracted files on disk, 
    # it simply gets the information directly from the subprocess.Popen() output.
    
    logger.info("Analyzing TOE file version...")
    
    # Cross-platform path handling
    if platform.system() == 'Windows':
        toeexpand_path = os.path.join(current_directory, "toeexpand", "toeexpand.exe")
        logger.debug(f"Using Windows toeexpand: {toeexpand_path}")
    else:  # Mac/Linux
        # For Mac, we'll use toeexpand from the first available TouchDesigner installation
        logger.debug("Looking for toeexpand in TouchDesigner installations...")
        td_apps = query_td_mac_applications()
        if td_apps:
            # Get the first available TouchDesigner app
            first_app = list(td_apps.values())[0]
            app_path = first_app['app_path']
            toeexpand_path = os.path.join(app_path, "Contents", "MacOS", "toeexpand")
            if DEBUG_MODE:
                logger.debug(f"Using toeexpand from: {app_path}")
            logger.debug(f"Toeexpand path: {toeexpand_path}")
        else:
            logger.error("❌ No TouchDesigner installation found for toeexpand")
            raise FileNotFoundError("No TouchDesigner installation found for toeexpand")
    
    # Check if toeexpand exists
    if not os.path.exists(toeexpand_path):
        logger.error(f"❌ toeexpand not found at: {toeexpand_path}")
        raise FileNotFoundError(f"toeexpand not found at: {toeexpand_path}")
    
    # Use cross-platform path
    command = f'"{toeexpand_path}" -b "{td_file_path}"'
    logger.debug(f"Running command: {command}")

    if DEBUG_MODE:
        logger.debug("Running toeexpand to analyze TOE file...")
    
    process = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out, err = process.communicate() # this is a blocking call, it will wait until the subprocess is finished.
    
    # Log the raw output for debugging
    raw_output = out.decode('utf-8')
    raw_error = err.decode('utf-8')
    
    logger.debug(f"toeexpand stdout: {repr(raw_output)}")
    if raw_error:
        logger.warning(f"toeexpand stderr: {repr(raw_error)}")
    
    if process.returncode != 0:
        logger.info(f"⚠️  toeexpand returned exit code {process.returncode} (this is often normal)")
        if raw_error:
            logger.debug(f"Error output: {raw_error}")
        # Don't fail immediately - toeexpand often returns 1 even with valid output
    
    build_info = raw_output # convert the output to a string.

    # strip \r from the build_info string.
    build_info = build_info.replace('\r','')
    logger.debug(f"Cleaned build_info: {repr(build_info)}")

    # Check if we have any useful output at all
    if not build_info or len(build_info.strip()) < 5:
        logger.error(f"❌ toeexpand produced no useful output")
        logger.error(f"stdout: {repr(raw_output)}")
        logger.error(f"stderr: {repr(raw_error)}")
        raise RuntimeError(f"toeexpand failed to produce output: {raw_error}")

    info_split = build_info.split('\n') # split the string into a list.
    logger.debug(f"Split info: {info_split}")
    
    # Filter out empty lines
    info_split = [line.strip() for line in info_split if line.strip()]
    logger.debug(f"Filtered info: {info_split}")
    
    if len(info_split) < 2:
        logger.error(f"❌ Unexpected toeexpand output format - need at least 2 lines")
        logger.error(f"Got: {info_split}")
        raise ValueError(f"Unexpected toeexpand output format: {info_split}")

    try:
        version_line = info_split[1]
        logger.debug(f"Version line: {version_line}")
        version_number = version_line.split(" ")[-1]
        build_option = f'TouchDesigner.{version_number}'
        
        logger.info(f"TOE file requires TouchDesigner {build_option}")
        
        return build_option
    except (IndexError, AttributeError) as e:
        logger.error(f"❌ Failed to parse version from toeexpand output: {e}")
        logger.error(f"Raw output was: {repr(build_info)}")
        raise ValueError(f"Failed to parse version from toeexpand output: {e}")


def generate_td_url(build_option):
    # Windows URLs:
    # https://download.derivative.ca/TouchDesigner088.62960.64-Bit.exe
    # https://download.derivative.ca/TouchDesigner099.2017.17040.64-Bit.exe
    # https://download.derivative.ca/TouchDesigner099.2018.28120.64-Bit.exe
    # https://download.derivative.ca/TouchDesigner099.2019.20700.exe
    # https://download.derivative.ca/TouchDesigner.2020.28110.exe
    # https://download.derivative.ca/TouchDesigner.2021.16960.exe
    # https://download.derivative.ca/TouchDesigner.2022.26590.exe
    
    # Mac URLs with architecture-specific suffixes:
    # https://download.derivative.ca/TouchDesigner.2022.26590.intel.dmg
    # https://download.derivative.ca/TouchDesigner.2022.26590.arm64.dmg

    
    split_options = build_option.split('.')
    product = split_options[0]
    year = split_options[1]
    build = split_options[2]
    
    # Platform and architecture-specific file extension
    if platform.system() == 'Windows':
        extension = '.exe'
        arch_suffix = ''
    else:  # Mac
        extension = '.dmg'
        # Detect Mac architecture
        machine = platform.machine().lower()
        if machine in ['arm64', 'aarch64']:
            arch_suffix = '.arm64'
        elif machine in ['x86_64', 'amd64']:
            arch_suffix = '.intel'
        else:
            # Default to intel for unknown architectures
            arch_suffix = '.intel'
            print(f"Warning: Unknown Mac architecture '{machine}', defaulting to Intel")

    # generate the url based on the build option and platform
    if year in [ "2017" , "2018" ] and platform.system() == 'Windows':
        url = f'https://download.derivative.ca/TouchDesigner099.{year}.{build}.64-Bit{extension}'

    elif year in [ "2019" ] and platform.system() == 'Windows':
        url = f'https://download.derivative.ca/TouchDesigner099.{year}.{build}{extension}'

    elif year == [ "2020" , "2021" , "2022"]:
        url = f'https://download.derivative.ca/TouchDesigner.{year}.{build}{arch_suffix}{extension}'

    else: # assume future years will use the same format as we have currently.
        url = f'https://download.derivative.ca/TouchDesigner.{year}.{build}{arch_suffix}{extension}'

    return url


# gather and generate some variables.
# Main execution starts

# build_info = inspect_toe() # old version
try:
    build_info = inspect_toe_v2()
    build_year = int(build_info.split('.')[1])
    if DEBUG_MODE:
        logger.debug(f"TOE file requires TouchDesigner year: {build_year}")
    
    td_url = generate_td_url(build_info)
    if DEBUG_MODE:
        logger.debug(f"Generated download URL: {td_url}")
    
    # Cross-platform file path
    td_filename = td_url.split("/")[-1]
    
    if platform.system() == 'Darwin':  # macOS
        # On macOS, save next to the TOE file to avoid permission issues
        toe_directory = os.path.dirname(os.path.abspath(td_file_path))
        td_uri = os.path.join(toe_directory, td_filename)
        logger.debug(f"macOS: Saving download next to TOE file")
        logger.debug(f"TOE file directory: {toe_directory}")
    else:  # Windows and other platforms
        # Keep original behavior for Windows
        td_uri = os.path.join(os.getcwd(), td_filename)
        logger.debug(f"Windows: Using current working directory")
    
    logger.debug(f"Download filename: {td_filename}")
    logger.debug(f"Local download path: {td_uri}")
    
except Exception as e:
    logger.error(f"❌ Failed to analyze TOE file: {e}")
    print(f"❌ Error analyzing TOE file: {e}")
    sys.exit(1)

# Platform-specific TouchDesigner discovery
logger.info("Checking for installed TouchDesigner versions...")
if platform.system() == 'Windows':
    td_key_id_dict = query_td_registry_entries()
else:  # Mac/Linux
    td_key_id_dict = query_td_mac_applications()

if DEBUG_MODE:
    logger.debug(f"Found {len(td_key_id_dict)} TouchDesigner installations")
    for key, info in td_key_id_dict.items():
        logger.debug(f"  • {key}: {info.get('executable', 'N/A')}")

# Maintain a stable, ordered list of available versions for keyboard navigation (consistent across OS)
def _parse_td_key_numeric(key: str):
    try:
        parts = key.split('.')
        year = int(parts[1]) if len(parts) > 1 else -1
        build = int(parts[2]) if len(parts) > 2 else -1
        return (year, build)
    except Exception:
        return (-1, -1)

version_keys = sorted(list(td_key_id_dict.keys()), key=_parse_td_key_numeric)

# Check if we have the required version
required_version_key = build_info
if required_version_key in td_key_id_dict:
    logger.info(f"Required version {required_version_key} is installed")
else:
    logger.info(f"Required version {required_version_key} not found - will download")

def cancel_countdown():
    global countdown_enabled
    countdown_enabled = False

def update_download_progress(b=1, bsize=1, tsize=None):
    global download_progress
    frac_progress = b * bsize / tsize
    frac_progress = max( min( frac_progress , 1 ) , 0 )
    download_progress = frac_progress
    dpg.set_value('download_progress_bar', download_progress)
    prog_text = str(download_progress*100)
    left = prog_text.split('.')[0]
    if len(prog_text.split('.')) > 1:
        right = prog_text.split('.')[1][0:1]
    else:
        right = '0'
    prog_text2 = f'{left}.{right}'
    dpg.configure_item('download_progress_bar', overlay=f'downloading {prog_text2}%')
    return

def start_download(sender, app_data):
    logger.info("Starting TouchDesigner download...")
    
    dpg.set_value("download_filter", 'b')

    retriever = urllib.request.urlretrieve

    try:
        # Download progress handled by start_download function
        result = retriever(td_url, filename=td_uri, reporthook=update_download_progress)
        
        # Check file size
        if os.path.exists(td_uri):
            file_size = os.path.getsize(td_uri)
            logger.info("Download completed successfully")
        else:
            logger.error("❌ Download completed but file not found!")

        dpg.configure_item('download_progress_bar', overlay=f'100%')
        dpg.set_value("download_filter", 'z')
        dpg.set_value("install_filter", 'a')
        
        # Download success already logged above
    
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        print(f"❌ Download error: {e}")
        dpg.set_value("download_filter", 'd')

    return


def install_touchdesigner_version(sender, app_data):
    logger.info("📦 Starting TouchDesigner installation...")
    logger.info("=" * 50)
    logger.info(f"💿 Installer file: {td_uri}")
    
    # Platform-specific installation handling
    try:
        if platform.system() == 'Windows':
            # Windows: Run the .exe installer silently
            install_command = [ 'start', '', '/WAIT', td_uri, ]
            logger.info(f"💻 Windows install command: {' '.join(install_command)}")
            process = subprocess.Popen(install_command, shell = True)
            logger.info(f"✅ Installer started with PID: {process.pid}")
        else:  # Mac
            # Mac: Open the .dmg file (this will mount it and show in Finder)
            # The user will need to manually drag the app to Applications
            install_command = ['open', td_uri]
            logger.info(f"🍎 macOS install command: {' '.join(install_command)}")
            process = subprocess.Popen(install_command)
            logger.info(f"✅ DMG opened with PID: {process.pid}")
            logger.info("ℹ️  User will need to manually drag TouchDesigner to Applications folder")
            
        logger.info("🎉 Installation process initiated!")
        logger.info("🔚 Closing TD Launcher...")
        
    except Exception as e:
        logger.error(f"❌ Installation failed: {e}")
        print(f"❌ Installation error: {e}")
        return
        
    exit_gui()
    return

def launch_toe_with_version(sender, app_data):
    radio_value = dpg.get_value( "td_version" )
    executable_path = td_key_id_dict[radio_value]['executable']
    
    logger.info("🚀 Launching TouchDesigner...")
    logger.info("=" * 50)
    logger.info(f"🎯 Selected version: {radio_value}")
    logger.info(f"📄 TOE file: {td_file_path}")
    logger.info(f"🔧 Executable: {executable_path}")
    
    try:
        if platform.system() == 'Windows':
            open_command = f'"{executable_path}" "{td_file_path}"'
            logger.info(f"💻 Windows launch command: {open_command}")
            process = subprocess.Popen(open_command, shell = True)
            logger.info(f"✅ Process started with PID: {process.pid}")
        else:  # Mac
            # On Mac, use 'open' command to launch the app with the file
            # open -a "/Applications/TouchDesigner.app" "file.toe"
            app_path = td_key_id_dict[radio_value]['app_path']
            open_command = ['open', '-a', app_path, td_file_path]
            logger.info(f"🍎 macOS launch command: {' '.join(open_command)}")
            process = subprocess.Popen(open_command)
            logger.info(f"✅ Process started with PID: {process.pid}")
            
        logger.info("🎉 TouchDesigner launch initiated successfully!")
        logger.info("🔚 Closing TD Launcher GUI...")
        
    except Exception as e:
        logger.error(f"❌ Failed to launch TouchDesigner: {e}")
        print(f"❌ Error launching TouchDesigner: {e}")
        return
        
    exit_gui()
    return

def exit_gui():
    # if os.path.isfile( td_uri ):
    #     os.remove( td_uri )
    logger.info("🔚 Shutting down GUI gracefully...")
    
    try:
        # On macOS, we need to stop the GUI loop more gently
        if platform.system() == 'Darwin':
            # Set a flag to stop the main loop instead of forcing exit
            global should_exit
            should_exit = True
            logger.info("✅ Exit flag set for graceful shutdown")
        else:
            # Windows can handle direct shutdown
            dpg.stop_dearpygui()
            dpg.destroy_context()
            logger.info("✅ GUI cleanup completed")
            sys.exit(0)
    except Exception as e:
        logger.warning(f"GUI cleanup warning: {e}")
        sys.exit(1)

# Keyboard navigation and actions
def move_selection(step: int):
    try:
        if not version_keys:
            return
        current_value = dpg.get_value("td_version")
        try:
            current_index = version_keys.index(current_value)
        except ValueError:
            current_index = 0
        new_index = (current_index + step) % len(version_keys)
        dpg.set_value("td_version", version_keys[new_index])
    except Exception as e:
        logger.debug(f"move_selection error: {e}")


def on_key_press(sender, app_data):
    # app_data is the key code
    try:
        # Cancel countdown on any key interaction
        cancel_countdown()

        key_code = app_data
        if key_code == getattr(dpg, 'mvKey_Up', None):
            move_selection(-1)
        elif key_code == getattr(dpg, 'mvKey_Down', None):
            move_selection(1)
        elif key_code in (
            getattr(dpg, 'mvKey_Enter', None),
            getattr(dpg, 'mvKey_Return', None),
            getattr(dpg, 'mvKey_KeyPadEnter', None),
            getattr(dpg, 'mvKey_KeypadEnter', None),
        ):
            launch_toe_with_version(sender, app_data)
        elif key_code == getattr(dpg, 'mvKey_Escape', None):
            exit_gui()
    except Exception as e:
        logger.debug(f"on_key_press error: {e}")

# build the UI
logger.info("🖥️  Initializing GUI...")
logger.info(f"📄 TOE file to display: {td_file_path}")
logger.info(f"🔧 Required version: {build_info}")
logger.info(f"📊 Available versions: {list(td_key_id_dict.keys())}")

dpg.create_context()

with dpg.handler_registry():
    dpg.add_mouse_click_handler(callback=cancel_countdown)
    dpg.add_key_press_handler(callback=on_key_press)


with dpg.window(tag="Primary Window"):

    dpg.add_text(f'Detected TD File: {td_file_path}', color=[50,255,0,255])

    if build_info not in list( td_key_id_dict.keys() ):
        dpg.add_text(f'Detected TD Version: {build_info} (NOT INSTALLED)', color=[255,50,0,255], tag="detected_version")
        with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit, row_background=True, resizable=False, no_host_extendX=False, hideable=True,
                   borders_innerV=False, delay_search=True, borders_outerV=False, borders_innerH=False,
                   borders_outerH=False, width=-1):
            dpg.add_table_column(width_stretch=True)
            # dpg.add_table_column(width_stretch=True)
            with dpg.table_row():
                with dpg.filter_set(id="download_filter"):
                    if build_year > 2019:
                        dpg.set_value("download_filter", 'a')
                    else:
                        dpg.set_value("download_filter", 'c')
                    dpg.add_button(label=f'Download : {build_info}', width=-1, callback=start_download, filter_key="a")
                    dpg.add_progress_bar(overlay=f'downloading 0.0%', tag='download_progress_bar', width=-1, default_value=download_progress, filter_key="b")
                    dpg.add_text(f'TD versions from 2019 and earlier are not yet compatible with this launcher.', color=[255,50,0,255], filter_key="c")
                    dpg.add_text(f'Error downloading build... go to derivative.ca to manually download', color=[255,50,0,255], filter_key="d")

        with dpg.filter_set(id="install_filter"):
            dpg.set_value("install_filter", 'z')
            dpg.add_button(label=f'Install : {build_info}', width=-1, enabled=True, filter_key="a", callback=install_touchdesigner_version)
            
    else:
        dpg.add_text(f'Detected TD Version: {build_info}', color=[50,255,0,255], tag="detected_version")

    dpg.add_separator()

    with dpg.child_window(height=200, width=-1):
        dpg.add_radio_button(version_keys, default_value=build_info, label='TD Version', tag="td_version", horizontal=False)

    dpg.add_separator()
    dpg.add_button(label=f'Open with selected version in {5} seconds', tag="launch_button", width=-1, height=-1, callback=launch_toe_with_version)

logger.info("🪟 Creating GUI viewport...")
dpg.create_viewport(title=f'TD Launcher {app_version}', width=800, height=442, resizable=True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

logger.info("✅ GUI initialized successfully!")

# record the starting time after the time intensive functions above have completed.
seconds_started = time.time()

if build_info not in list( td_key_id_dict.keys() ):
    countdown_enabled = False
    logger.info("⏸️  Auto-launch disabled - required version not installed")
else:
    logger.info("⏰ Auto-launch enabled - will launch in 5 seconds")

logger.info("🔄 Starting main GUI loop...")

while dpg.is_dearpygui_running():
    
    # Check for graceful exit flag (macOS)
    if should_exit:
        logger.info("🔚 Exit flag detected, shutting down gracefully...")
        dpg.stop_dearpygui()
        break

    if countdown_enabled == True:

        # calc elapsed time.
        num_sec_elapsed = int((time.time() - seconds_started) * 10) / 10
        num_sec_remaining = max( num_sec_until_autostart - (num_sec_elapsed*countdown_enabled) , 0 )
        num_sec_remaining_label = str(num_sec_remaining)[0:3]

        if dpg.does_item_exist("launch_button"):
            dpg.configure_item("launch_button", label=f'Open with selected version in {num_sec_remaining_label} seconds')
        
        # if countdown has ended, start toe
        if num_sec_remaining <= 0:
            logger.info(f"⏰ Auto-launch timeout reached, launching {build_info}")
            launch_toe_with_version({}, {})
        
    else:

        if dpg.does_item_exist("launch_button"):
            dpg.configure_item("launch_button", label=f'Open with selected version')

    dpg.render_dearpygui_frame()

else:
    logger.info("🔚 GUI loop ended, cleaning up...")
    # if os.path.isfile( td_uri ):
    #     os.remove( td_uri )
    
    try:
        dpg.destroy_context()
        logger.info("✅ GUI context destroyed")
    except Exception as e:
        logger.warning(f"GUI cleanup warning: {e}")
    
    logger.info("👋 TD Launcher shutdown complete")
    
    # Final graceful exit
    if platform.system() == 'Darwin':
        logger.info("🍎 macOS graceful exit")
        sys.exit(0)
    else:
        logger.info("💻 Windows exit")


