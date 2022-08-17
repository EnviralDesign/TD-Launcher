# TD_Launcher
A launcher / bootstrapper for launching TouchDesigner projects (.toe files) with the correct version automatically.

### Toe autolaunch
![image](https://user-images.githubusercontent.com/10091486/185008821-c4294500-7e1b-47d2-b3df-881519591de5.png)

### TD Download and Install from Launcher
![image](https://user-images.githubusercontent.com/10091486/185009037-6569848a-dd25-4766-a73e-23a770b5e36b.png)
![image](https://user-images.githubusercontent.com/10091486/185009082-c09f20f5-01b6-4d8e-9a42-9e820844a9ec.png)
![image](https://user-images.githubusercontent.com/10091486/185009223-7d1f5840-02cb-4eae-b6b8-a26d4c8e032a.png)

### Older Builds not yet supported
![image](https://user-images.githubusercontent.com/10091486/185009295-71c275b8-c295-44d5-ac47-98c514e2f115.png)



## What's this for


If you work on a lot of TD projects, or support many older projects you know the pain of having to manage / guess / remember which version something was built in. A real pain if you accidentally upgrade your projects build and lose work when trying to downgrade back again!

## How this works
This tool scans your registry for TouchDesigner entries, and builds a list of available TD executables / installs that can potentially be used. It then analyzes the .toe file and loads the GUI with the appropriate option selected, and starts a 5 second timer.

If you interupt it by clicking anywhere, you can choose a different version or cancel. If you leave it undisturbed, it will launch after 5 sec in the detected version.

If the required version of Touch is not found, the launcher will not launch anything automatically, and will wait for your input with the required build highlighted in red.

## How to use
Download the installer from the releases page on the right, and set windows to open your toe files with that by default. Doubleclicking on toes from that point onwards will launch them with the Launcher. You can also drag and drop toe files onto the launcher.

## How to build
This was built with Python 3.10. Pyinstaller, and the wonderful [DearPyGui](https://github.com/hoffstadt/DearPyGui) for UI. All other libraries used were defaults / builtins.

If you want to build, download this repo and unzip the py directory inside py.zip into the root of the repo. This is a fully python install, with Pyinstaller and DearPyGui, and any other dependancies installed.

You can test the launcher by running td_launcher.bat, and you can rebuild the single executable by running BUILD.bat.

Once the exe is generated at TD_Launcher\dist\td_launcher.exe, you can optionally package this into an installer exe using inno, in the inno directory.

---

If you have any issues, please post a bug issue here.
