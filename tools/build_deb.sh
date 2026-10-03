#!/usr/bin/env bash
# 由 PyInstaller onedir 产物（dist/xiangqi-pyside）生成 deb
# 用法: tools/build_deb.sh [版本]
set -euo pipefail

APP_NAME=xiangqi-pyside
APP_VERSION="${1:-0.1.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist/$APP_NAME"
ROOTFS="$ROOT/debroot"

[ -x "$DIST/$APP_NAME" ] || { echo "缺少 $DIST/$APP_NAME，请先运行 PyInstaller"; exit 1; }

rm -rf "$ROOTFS"
mkdir -p "$ROOTFS/DEBIAN" "$ROOTFS/usr/lib" "$ROOTFS/usr/bin" \
         "$ROOTFS/usr/share/applications" \
         "$ROOTFS/usr/share/icons/hicolor/512x512/apps"

cp -r "$DIST" "$ROOTFS/usr/lib/$APP_NAME"
cat > "$ROOTFS/usr/bin/$APP_NAME" <<EOF
#!/bin/sh
exec /usr/lib/$APP_NAME/$APP_NAME "\$@"
EOF
chmod 755 "$ROOTFS/usr/bin/$APP_NAME"
cp "$ROOT/tools/$APP_NAME.desktop" "$ROOTFS/usr/share/applications/"
cp "$ROOT/tools/xiangqi.png" "$ROOTFS/usr/share/icons/hicolor/512x512/apps/xiangqi.png"

INSTALLED_SIZE="$(du -sk "$ROOTFS/usr" | cut -f1)"
cat > "$ROOTFS/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $APP_VERSION
Section: games
Priority: optional
Architecture: amd64
Maintainer: Xiangqi Dev <dev@local>
Installed-Size: $INSTALLED_SIZE
Depends: libc6 (>= 2.34), libxcb-cursor0
Description: 中国象棋（Python/PySide6 版）
 Chinese Chess built with Python and PySide6 (Qt 6.8.3), rule engine + AI.
EOF

dpkg-deb --build --root-owner-group "$ROOTFS" "$ROOT/${APP_NAME}_${APP_VERSION}_amd64.deb"
echo "已生成 ${APP_NAME}_${APP_VERSION}_amd64.deb"
