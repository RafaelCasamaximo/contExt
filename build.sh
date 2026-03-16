#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SPEC_FILE="$PROJECT_DIR/packaging/pyinstaller/ContExt.spec"
RELEASE_DIR="$PROJECT_DIR/release"
WORK_DIR="$RELEASE_DIR/linux-x64"
DIST_DIR="$WORK_DIR/dist"
BUILD_DIR="$WORK_DIR/build"
CONFIG_DIR="$WORK_DIR/config"
ARTIFACT_DIR="$RELEASE_DIR/ContExt-linux-x64"
ARTIFACT_FILE="$RELEASE_DIR/ContExt-linux-x64.tar.gz"

if [ "$(uname -s)" != "Linux" ]; then
  echo "build.sh must be run on Linux." >&2
  exit 1
fi

rm -rf "$WORK_DIR" "$ARTIFACT_DIR" "$ARTIFACT_FILE"
mkdir -p "$DIST_DIR" "$BUILD_DIR" "$CONFIG_DIR" "$ARTIFACT_DIR"
export PYINSTALLER_CONFIG_DIR="$CONFIG_DIR"

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$SPEC_FILE"

cp "$DIST_DIR/ContExt" "$ARTIFACT_DIR/ContExt"
chmod +x "$ARTIFACT_DIR/ContExt"
tar -C "$RELEASE_DIR" -czf "$ARTIFACT_FILE" "ContExt-linux-x64"

echo "Created $ARTIFACT_FILE"
