rm -rf release
mkdir release
cd release
rm -rf release-linux_64x
mkdir release-linux_64x
cd release-linux_64x
pyinstaller --onefile ../../main.py --name ContExt --icon ../../icons/Icon.ico
cd ..
cd ..