#!/usr/bin/env python3
"""
Test script for Mac TouchDesigner discovery functionality
This can be run independently to test the Mac-specific parts of td_launcher.py
"""

import os
import platform
import plistlib
import glob

def query_td_mac_applications():
    """Mac version: scan /Applications for TouchDesigner apps and extract version info from Info.plist"""
    td_matching_apps = []
    applications_dir = "/Applications"
    
    # Look for TouchDesigner applications
    td_pattern = os.path.join(applications_dir, "TouchDesigner*")
    td_apps = glob.glob(td_pattern)
    
    print(f"Found {len(td_apps)} TouchDesigner-like applications:")
    for app in td_apps:
        print(f"  - {app}")
    
    td_key_id_dict = {}
    
    for app_path in td_apps:
        if not app_path.endswith('.app'):
            print(f"Skipping {app_path} (not a .app bundle)")
            continue
            
        app_name = os.path.basename(app_path)
        info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
        
        try:
            # Read the Info.plist file
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            # Extract version information
            bundle_version = plist_data.get('CFBundleVersion', '')
            bundle_name = plist_data.get('CFBundleName', app_name)
            bundle_identifier = plist_data.get('CFBundleIdentifier', 'Unknown')
            
            print(f"\nApp: {app_name}")
            print(f"  Bundle Name: {bundle_name}")
            print(f"  Bundle Version: {bundle_version}")
            print(f"  Bundle Identifier: {bundle_identifier}")
            
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
                    toeexpand_path = os.path.join(app_path, "Contents", "MacOS", "toeexpand")
                    
                    # Check if the executable exists
                    executable_exists = os.path.exists(executable_path)
                    toeexpand_exists = os.path.exists(toeexpand_path)
                    
                    print(f"  Generated Key: {td_key}")
                    print(f"  Executable Path: {executable_path}")
                    print(f"  Executable Exists: {executable_exists}")
                    print(f"  toeexpand Path: {toeexpand_path}")
                    print(f"  toeexpand Exists: {toeexpand_exists}")
                    
                    td_key_id_dict[td_key] = {
                        'executable': executable_path,
                        'app_path': app_path,
                        'bundle_version': bundle_version,
                        'executable_exists': executable_exists,
                        'toeexpand_exists': toeexpand_exists
                    }
                    
        except (FileNotFoundError, plistlib.InvalidFileException, KeyError) as e:
            print(f"Could not read Info.plist for {app_path}: {e}")
            continue
    
    return td_key_id_dict

def test_architecture_detection():
    """Test Mac architecture detection for download URLs"""
    machine = platform.machine().lower()
    print(f"Machine Architecture: {machine}")
    
    if machine in ['arm64', 'aarch64']:
        arch_suffix = '.arm64'
        arch_name = "Apple Silicon (M1/M2/M3)"
    elif machine in ['x86_64', 'amd64']:
        arch_suffix = '.intel'
        arch_name = "Intel"
    else:
        arch_suffix = '.intel'
        arch_name = f"Unknown ({machine}) - defaulting to Intel"
    
    print(f"Detected Architecture: {arch_name}")
    print(f"Download URL Suffix: {arch_suffix}")
    
    # Example URL generation
    example_url = f"https://download.derivative.ca/TouchDesigner.2023.11290{arch_suffix}.dmg"
    print(f"Example Download URL: {example_url}")
    
    return arch_suffix

if __name__ == "__main__":
    print("Testing Mac TouchDesigner Discovery")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print(f"Platform Release: {platform.release()}")
    print()
    
    # Test architecture detection
    test_architecture_detection()
    print()
    
    if platform.system() != 'Darwin':
        print("Warning: This test is designed for Mac OS (Darwin)")
        print("Current platform may not have the expected directory structure")
        print()
    
    td_apps = query_td_mac_applications()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Found {len(td_apps)} valid TouchDesigner installations:")
    
    for key, info in td_apps.items():
        print(f"\n{key}:")
        print(f"  App: {info['app_path']}")
        print(f"  Version: {info['bundle_version']}")
        print(f"  Ready to use: {info['executable_exists'] and info['toeexpand_exists']}")
        
    if not td_apps:
        print("No TouchDesigner installations found.")
        print("Make sure TouchDesigner is installed in /Applications/")