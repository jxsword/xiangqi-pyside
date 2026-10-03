# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置（onedir）：PySide6 QWidget 程序
import sys
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('xiangqi')
ICON = '../tools/xiangqi.ico' if sys.platform == 'win32' else '../tools/xiangqi.png'

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D',
              'PySide6.QtWebEngineCore', 'PySide6.QtMultimedia',
              'PySide6.Qt3DCore', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
              'PySide6.QtPdf', 'PySide6.QtVirtualKeyboard'],
    noarchive=False,
)

# QWidget 程序不需要 QML/Quick/PDF/虚拟键盘等原生库与插件，剔除瘦身
_DROP_LIB = ('Qt6Qml', 'Qt6Quick', 'Qt6QmlMeta', 'Qt6QmlModels',
             'Qt6QmlWorkerScript', 'Qt6VirtualKeyboard', 'Qt6Pdf')
_DROP_PATH = ('PySide6/Qt/qml/', 'Qt/qml/', 'qmltooling/',
              'platforminputcontexts/qtvirtualkeyboard', 'QtQuick/')


def _dropped(name: str) -> bool:
    n = name.replace('\\', '/')
    return (any(d in n for d in _DROP_LIB)
            or any(d in n for d in _DROP_PATH))


a.binaries = [x for x in a.binaries if not _dropped(x[0])]
a.datas = [x for x in a.datas if not _dropped(x[0])]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='xiangqi-pyside',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    console=False,
    icon=ICON,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False,
    name='xiangqi-pyside',
)
