#!/usr/bin/env python3
"""
Test script for URL generation with architecture detection
"""

import platform

def generate_td_url_test(build_option):
    """Test version of the URL generation function"""
    # Simulate the same logic as in td_launcher.py
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

    elif year in [ "2020" , "2021" , "2022"]:
        url = f'https://download.derivative.ca/TouchDesigner.{year}.{build}{arch_suffix}{extension}'

    else: # assume future years will use the same format as we have currently.
        url = f'https://download.derivative.ca/TouchDesigner.{year}.{build}{arch_suffix}{extension}'

    return url

if __name__ == "__main__":
    print("Testing TouchDesigner URL Generation")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print()
    
    # Test various TD versions
    test_versions = [
        "TouchDesigner.2020.28110",
        "TouchDesigner.2021.16960", 
        "TouchDesigner.2022.26590",
        "TouchDesigner.2023.11290",
        "TouchDesigner.2024.10000"
    ]
    
    for version in test_versions:
        url = generate_td_url_test(version)
        print(f"{version}")
        print(f"  → {url}")
        print()
    
    # Test older versions if on Windows
    if platform.system() == 'Windows':
        older_versions = [
            "TouchDesigner.2017.17040",
            "TouchDesigner.2018.28120", 
            "TouchDesigner.2019.20700"
        ]
        
        print("Older Windows versions:")
        for version in older_versions:
            url = generate_td_url_test(version)
            print(f"{version}")
            print(f"  → {url}")
            print()