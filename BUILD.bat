
@echo off
setlocal

set PYTHON_EXECUTABLE=.\py\python.exe

%PYTHON_EXECUTABLE% .\py\Scripts\pyinstaller.exe --noconfirm --log-level=WARN ^
--onefile --nowindow ^
--windowed ^
--name="td_launcher" ^
--icon="td_launcher.ico" ^
--add-binary="toeexpand/toeexpand.exe;toeexpand" ^
--add-binary="test.toe;." ^
--add-binary="toeexpand/iconv.dll;toeexpand" ^
--add-binary="toeexpand/icudt59.dll;toeexpand" ^
--add-binary="toeexpand/icuuc59.dll;toeexpand" ^
--add-binary="toeexpand/libcurl.dll;toeexpand" ^
--add-binary="toeexpand/libcurl-x64.dll;toeexpand" ^
--add-binary="toeexpand/zlib1.dll;toeexpand" ^
.\td_launcher.py

endlocal