#!/usr/bin/env bash
# 由 PyInstaller onedir 产物（dist/xiangqi-pyside）生成 AppImage
# 用法: tools/build_appimage.sh [版本]
set -euo pipefail

APP_NAME=xiangqi-pyside
APP_VERSION="${1:-0.1.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist/$APP_NAME"
APPDIR="$ROOT/AppDir"
TOOL="$ROOT/tools/appimagetool"

[ -x "$DIST/$APP_NAME" ] || { echo "缺少 $DIST/$APP_NAME，请先运行 PyInstaller"; exit 1; }

# appimagetool 不存在则下载（AppImageKit 官方 release）
if [ ! -x "$TOOL" ]; then
  echo "下载 appimagetool ..."
  curl -sSL -o "$TOOL" \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "$TOOL"
fi

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/512x512/apps"

cp -r "$DIST" "$APPDIR/usr/bin/$APP_NAME"
cp "$ROOT/tools/$APP_NAME.desktop" "$APPDIR/usr/share/applications/"
cp "$ROOT/tools/xiangqi.png" "$APPDIR/usr/share/icons/hicolor/512x512/apps/xiangqi.png"
# AppImage 规范要求根目录也有一份 desktop 与图标
cp "$ROOT/tools/$APP_NAME.desktop" "$APPDIR/$APP_NAME.desktop"
cp "$ROOT/tools/xiangqi.png" "$APPDIR/xiangqi.png"

cat > "$APPDIR/AppRun" <<EOF
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\$0")")"
export PATH="\$HERE/usr/bin:\$PATH"
exec "\$HERE/usr/bin/$APP_NAME/$APP_NAME" "\$@"
EOF
chmod +x "$APPDIR/AppRun"

export APPIMAGE_EXTRACT_AND_RUN=1
ARCH=x86_64 "$TOOL" "$APPDIR" "$ROOT/${APP_NAME}_${APP_VERSION}_amd64.AppImage"
echo "已生成 ${APP_NAME}_${APP_VERSION}_amd64.AppImage"
