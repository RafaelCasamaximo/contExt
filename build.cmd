rmdir /s release
md release
cd release
rmdir /s release-win
md release-windows_64x
cd release-windows_64x
python -m PyInstaller --noconsole --onefile --windowed ../../main.py --name ContExt --icon ../../icons/Icon.ico
cd dist
Xcopy .\..\..\..\icons .\icons /E /H /C /I
Xcopy .\..\..\..\fonts .\fonts /E /H /C /I
cd ..
cd ..
cd ..