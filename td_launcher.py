import dearpygui.dearpygui as dpg
import winreg
import subprocess
import os
from pathlib import Path
import shutil
import sys
import time

num_sec_until_autostart = 5
current_directory = os.path.dirname(__file__)
countdown_enabled = True

# define some user args.
if len(sys.argv) >= 2:
    td_file_path = sys.argv[1] # this gets passed in as argument
else:
    td_file_path = f'{current_directory}\\test.toe'

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


def inspect_toe():
    # current_directory = os.getcwd() # doesn't work right with command like args, 
    td_file_path_osstyle = td_file_path.replace('/','\\')
    command = f'"{current_directory}\\toeexpand\\toeexpand.exe" "{td_file_path_osstyle}"'

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
    build_option = f'TouchDesigner.{info_split[1].split(" ")[-1]}'
    
    return build_option

# get build info about toe file.
build_info = inspect_toe()

# get touchdesigner executable entries from registry.
td_key_id_dict = query_td_registry_entries()

def cancel_countdown():
    global countdown_enabled
    countdown_enabled = False


def launch_toe_with_version(sender, app_data):
    radio_value = dpg.get_value( "td_version" )
    executable_path = td_key_id_dict[radio_value]['executable']
    open_command = f'"{executable_path}" "{td_file_path}"'
    subprocess.Popen(open_command, shell = True)
    dpg.stop_dearpygui()
    dpg.destroy_context()
    quit()
    return

# build the UI
dpg.create_context()

with dpg.handler_registry():
    dpg.add_mouse_click_handler(callback=cancel_countdown)

with dpg.window(tag="Primary Window"):

    dpg.add_text(f'Detected TD File: {td_file_path}', color=[50,255,0,255])

    if build_info not in list( td_key_id_dict.keys() ):
        dpg.add_text(f'Detected TD Version: {build_info} (NOT INSTALLED)', color=[255,50,0,255], tag="detected_version")
    else:
        dpg.add_text(f'Detected TD Version: {build_info}', color=[50,255,0,255], tag="detected_version")

    dpg.add_separator()

    with dpg.child_window(height=200):
        dpg.add_radio_button(list(td_key_id_dict.keys()), default_value=build_info, label='TD Version', tag="td_version", horizontal=False)

    dpg.add_separator()
    dpg.add_button(label=f'Open with selected version in {5} seconds', tag="launch_button", width=800, height=79, callback=launch_toe_with_version)

dpg.create_viewport(title='Multi Version TD Launcher', width=800, height=390, resizable=False)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

# record the starting time after the time intensive functions above have completed.
seconds_started = time.time()

# print(build_info)
# print(td_key_id_dict.keys())
if build_info not in list( td_key_id_dict.keys() ):
    countdown_enabled = False
    # dpg.configure_item("detected_version", label = f'Detected TD Version: {build_info} (NOT INSTALLED)' )
    # dpg.configure_item("detected_version", label = f'Detected TD Version: {build_info} (NOT INSTALLED)', color=[255,50,0,255] )

# dpg.start_dearpygui() # can use this if we don't need to access / use main render loop.
while dpg.is_dearpygui_running():

    if countdown_enabled == True:

        # calc elapsed time.
        num_sec_elapsed = int((time.time() - seconds_started) * 10) / 10
        num_sec_remaining = max( num_sec_until_autostart - (num_sec_elapsed*countdown_enabled) , 0 )
        num_sec_remaining_label = str(num_sec_remaining)[0:3]

        if dpg.does_item_exist("launch_button"):
            dpg.configure_item("launch_button", label=f'Open with selected version in {num_sec_remaining_label} seconds')
        
        # if countdown has ended, start toe
        if num_sec_remaining <= 0:
            launch_toe_with_version({}, {})
        
    else:

        if dpg.does_item_exist("launch_button"):
            dpg.configure_item("launch_button", label=f'Open with selected version')

    dpg.render_dearpygui_frame()

dpg.destroy_context()


