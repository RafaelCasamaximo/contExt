if exist release rmdir /s /q release
md release
cd release
if exist release-windows_64x rmdir /s /q release-windows_64x
md release-windows_64x
cd release-windows_64x
python -m PyInstaller -F --collect-submodules=pydicom --noconsole --onefile --windowed --paths ../../src --add-data ../../icons;icons --add-data ../../fonts;fonts --add-data ../../src/context/ui/translations.json;context/ui ../../main.py --name ContExt --icon ../../icons/Icon.ico
cd ..
cd ..
