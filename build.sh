rm -rf release
mkdir release
cd release
pyinstaller --onefile ../main.py
cd ..