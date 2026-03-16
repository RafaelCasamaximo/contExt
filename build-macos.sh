#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SPEC_FILE="$PROJECT_DIR/packaging/pyinstaller/ContExt.spec"
RELEASE_DIR="$PROJECT_DIR/release"
WORK_DIR="$RELEASE_DIR/macos-universal2"
DIST_DIR="$WORK_DIR/dist"
BUILD_DIR="$WORK_DIR/build"
CONFIG_DIR="$WORK_DIR/config"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "build-macos.sh must be run on macOS." >&2
  exit 1
fi

TARGET_ARCH="${CONTEXT_TARGET_ARCH:-$(uname -m)}"
case "$TARGET_ARCH" in
  arm64)
    ARTIFACT_SUFFIX="arm64"
    ;;
  x86_64)
    ARTIFACT_SUFFIX="x64"
    ;;
  universal2)
    ARTIFACT_SUFFIX="universal2"
    ;;
  *)
    echo "Unsupported CONTEXT_TARGET_ARCH: $TARGET_ARCH" >&2
    exit 1
    ;;
esac

WORK_DIR="$RELEASE_DIR/macos-$ARTIFACT_SUFFIX"
DIST_DIR="$WORK_DIR/dist"
BUILD_DIR="$WORK_DIR/build"
CONFIG_DIR="$WORK_DIR/config"
ARTIFACT_DIR="$RELEASE_DIR/ContExt-macos-$ARTIFACT_SUFFIX"
ARTIFACT_FILE="$RELEASE_DIR/ContExt-macos-$ARTIFACT_SUFFIX.app.zip"

rm -rf "$WORK_DIR" "$ARTIFACT_DIR" "$ARTIFACT_FILE"
mkdir -p "$DIST_DIR" "$BUILD_DIR" "$CONFIG_DIR" "$ARTIFACT_DIR"
export PYINSTALLER_CONFIG_DIR="$CONFIG_DIR"
export CONTEXT_TARGET_ARCH="$TARGET_ARCH"

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$SPEC_FILE"

cp -R "$DIST_DIR/ContExt.app" "$ARTIFACT_DIR/ContExt.app"
ditto -c -k --sequesterRsrc --keepParent "$ARTIFACT_DIR/ContExt.app" "$ARTIFACT_FILE"

echo "Created $ARTIFACT_FILE"
