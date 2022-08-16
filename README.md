# TD_Launcher

## What's this for
This application is a simple bootstrapper for launching TouchDesigner projects (.toe files) with the correct version automatically.

If you work on a lot of TD projects, or support many older projects you know the pain of having to manage / guess / remember which version something was built in. A real pain if you accidentally upgrade your projects build and lose work when trying to downgrade back again!

## How this works
This tool scans your registry for TouchDesigner entries, and builds a list of available TD executables / installs that can potentially be used. It then analyzes the .toe file and loads the GUI with the appropriate option selected, and starts a 5 second timer.

If you interupt it by clicking anywhere, you can choose a different version or cancel. If you leave it undisturbed, it will launch after 5 sec in the detected version.

## How to use
Simply download the .exe from the releases page on the right, and set windows to open your toe files with that by default. If you want to give it a trial run, just drag any .toe file onto the exe to test it manually.

## How to build
This was built with Python 3.10. Pyinstaller, and the wonderful [DearPyGui](https://github.com/hoffstadt/DearPyGui) for UI. All other libraries used were defaults / builtins.

If you want to build, download this repo and unzip the py directory inside py.zip into the root of the repo. This is a fully python install, with Pyinstaller and DearPyGui installed.

You can test the launcher by running td_launcher.bat, and you can rebuild the single executable by running BUILD.bat.

---

If you have any issues, please post a bug issue here.
