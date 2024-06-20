import dearpygui.dearpygui as dpg
import winreg
import subprocess
import os
from pathlib import Path
import shutil
import sys
import time
import urllib.request

app_version = '1.0.4'

num_sec_until_autostart = 5
current_directory = os.path.dirname(__file__)
countdown_enabled = True
download_progress = 0.0

# define some user args.
if len(sys.argv) >= 2:
    td_file_path = sys.argv[1] # this gets passed in as argument
else:
    td_file_path = f'{current_directory}\\test.toe'
    # td_file_path = f'{current_directory}\\test2.toe'
    # td_file_path = f'{current_directory}\\test3.toe'

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
        if "TouchDesigner" in key_name and key_name.split('.')[-1].isdigit():
            td_matching_keys += [ key_name ]
    
    td_matching_keys = sorted(td_matching_keys)

    td_key_id_dict = { k:{} for k in td_matching_keys }
    for k,v in td_key_id_dict.items():
        entry_val = winreg.QueryValue(reg, f'{k}\\shell\\open\\command')
        td_key_id_dict[k]['executable'] = entry_val.split('"')[1]
    
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
    # it simply gets the information dorectly from the subprocess.Popen() output.
    # the subprocess call function is a bit different, it should follow this template: toeexpand -b C:\repos\TD_Launcher\test.toe

    td_file_path_osstyle = td_file_path.replace('/','\\')
    command = f'"{current_directory}\\toeexpand\\toeexpand.exe" -b "{td_file_path_osstyle}"'

    process = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out, err = process.communicate() # this is a blocking call, it will wait until the subprocess is finished.
    build_info = out.decode('utf-8') # convert the output to a string.

    # strip \r from the build_info string.
    build_info = build_info.replace('\r','')

    info_split = build_info.split('\n') # split the string into a list.

    build_option = f'TouchDesigner.{info_split[1].split(" ")[-1]}' # this is the build option we want to use.

    return build_option


def generate_td_url(build_option):
    # https://download.derivative.ca/TouchDesigner088.62960.64-Bit.exe
    # https://download.derivative.ca/TouchDesigner099.2017.17040.64-Bit.exe
    # https://download.derivative.ca/TouchDesigner099.2018.28120.64-Bit.exe
    # https://download.derivative.ca/TouchDesigner099.2019.20700.exe
    # https://download.derivative.ca/TouchDesigner.2020.28110.exe
    # https://download.derivative.ca/TouchDesigner.2021.16960.exe
    # https://download.derivative.ca/TouchDesigner.2022.26590.exe

    
    split_options = build_option.split('.')
    product = split_options[0]
    year = split_options[1]
    build = split_options[2]

    # generate the url based on the build option.
    if year in [ "2017" , "2018" ]:
        url = f'https://download.derivative.ca/TouchDesigner099.{year}.{build}.64-Bit.exe'

    elif year in [ "2019" ]:
        url = f'https://download.derivative.ca/TouchDesigner099.{year}.{build}.exe'

    elif year == [ "2020" , "2021" , "2022"]:
        url = f'https://download.derivative.ca/TouchDesigner.{year}.{build}.exe'

    else: # assume future years will use the same format as we have currently.
        url = f'https://download.derivative.ca/TouchDesigner.{year}.{build}.exe'

    return url


# gather and generate some variables.
# build_info = inspect_toe() # old version
build_info = inspect_toe_v2()
build_year = int(build_info.split('.')[1])
td_url = generate_td_url(build_info)
td_uri = f'{os.getcwd()}\\{td_url.split("/")[-1]}'
td_key_id_dict = query_td_registry_entries()

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
    dpg.set_value("download_filter", 'b')

    retriever = urllib.request.urlretrieve

    try:
        result = retriever(td_url, filename=td_uri, reporthook=update_download_progress)

        dpg.configure_item('download_progress_bar', overlay=f'100%')
        dpg.set_value("download_filter", 'z')
        dpg.set_value("install_filter", 'a')
    
    except Exception as e:
        
        dpg.set_value("download_filter", 'd')

    return


def install_touchdesigner_version(sender, app_data):
    # print(sender,app_data)
    # start "" /WAIT %td_installer_executable_abs% /SILENT /LOG="td_installation_Log.txt" /DIR="%td_path_abs%" /SUPPRESSMSGBOXES
    install_command = [ 'start', '', '/WAIT', td_uri, ]
    subprocess.Popen(install_command, shell = True)
    exit_gui()
    return

def launch_toe_with_version(sender, app_data):
    radio_value = dpg.get_value( "td_version" )
    executable_path = td_key_id_dict[radio_value]['executable']
    open_command = f'"{executable_path}" "{td_file_path}"'
    subprocess.Popen(open_command, shell = True)
    exit_gui()
    return

def exit_gui():
    # if os.path.isfile( td_uri ):
    #     os.remove( td_uri )
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
        dpg.add_radio_button(list(td_key_id_dict.keys()), default_value=build_info, label='TD Version', tag="td_version", horizontal=False)

    dpg.add_separator()
    dpg.add_button(label=f'Open with selected version in {5} seconds', tag="launch_button", width=-1, height=-1, callback=launch_toe_with_version)

dpg.create_viewport(title=f'TD Launcher {app_version}', width=800, height=442, resizable=True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

# record the starting time after the time intensive functions above have completed.
seconds_started = time.time()


if build_info not in list( td_key_id_dict.keys() ):
    countdown_enabled = False


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

else:
    # if os.path.isfile( td_uri ):
    #     os.remove( td_uri )
    dpg.destroy_context()


