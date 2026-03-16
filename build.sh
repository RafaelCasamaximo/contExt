set -eu

rm -rf release
mkdir release
cd release
rm -rf release-linux_64x
mkdir release-linux_64x
cd release-linux_64x
python3 -m PyInstaller --onefile -F \
  --collect-submodules=pydicom \
  --paths ../../src \
  --add-data ../../icons:icons \
  --add-data ../../fonts:fonts \
  --add-data ../../src/context/ui/translations.json:context/ui \
  ../../main.py \
  --name ContExt \
  --icon ../../icons/Icon.ico
cd ..
cd ..
