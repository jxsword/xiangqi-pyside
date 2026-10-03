# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置（onedir）：PySide6 QWidget 程序
import os
import sys
from PyInstaller.utils.hooks import (
    collect_submodules, collect_dynamic_libs, collect_data_files,
)

WIN = sys.platform == 'win32'
DARWIN = sys.platform == 'darwin'
hiddenimports = collect_submodules('xiangqi')
if WIN:
    ICON = '../tools/xiangqi.ico'
elif DARWIN:
    ICON = None  # macOS 需 .icns，暂用 PyInstaller 默认图标
else:
    ICON = '../tools/xiangqi.png'

# QWidget 程序不需要 QML/Quick/PDF/虚拟键盘等
_DROP_LIB = ('Qt6Qml', 'Qt6Quick', 'Qt6QmlMeta', 'Qt6QmlModels',
             'Qt6QmlWorkerScript', 'Qt6VirtualKeyboard', 'Qt6Pdf')
_DROP_PATH = ('PySide6/Qt/qml/', 'Qt/qml/', 'qmltooling/',
              'platforminputcontexts/qtvirtualkeyboard', 'QtQuick/')

# Windows 下显式收集的 Qt 运行库（wine 交叉构建时 QtLibraryInfo 子进程查询会失败，
# 标准 hook 无法自动发现插件，故在 win32 下改为显式白名单收集）
_KEEP_QT_DLL = (
    'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'Qt6Network.dll',
    'Qt6OpenGL.dll', 'Qt6Svg.dll',
)
_KEEP_VC_PREFIX = ('concrt140', 'msvcp140', 'vcruntime140')
_KEEP_PLUGIN_DIRS = (
    'platforms', 'imageformats', 'styles', 'iconengines',
    'tls', 'generic', 'networkinformation',
)

extra_binaries = []
extra_datas = []
if WIN:
    # shiboken6 动态库
    extra_binaries += collect_dynamic_libs('shiboken6')
    # PySide6 扁平布局：Qt6*.dll 与 VC 运行时位于 PySide6/ 根目录
    for src, dest in collect_dynamic_libs('PySide6'):
        base = os.path.basename(src)
        if base in _KEEP_QT_DLL or base.startswith(_KEEP_VC_PREFIX):
            extra_binaries.append((src, dest))
    # 插件（按白名单目录）放到 PySide6/plugins（rthook 以 QT_PLUGIN_PATH 指向此处）
    for src, dest in collect_data_files('PySide6'):
        norm = src.replace('\\', '/')
        if '/plugins/' in norm:
            sub = norm.split('/plugins/')[1].split('/')[0]
            if sub in _KEEP_PLUGIN_DIRS:
                extra_datas.append((src, dest))

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=extra_binaries,
    datas=extra_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D',
              'PySide6.QtWebEngineCore', 'PySide6.QtMultimedia',
              'PySide6.Qt3DCore', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
              'PySide6.QtPdf', 'PySide6.QtVirtualKeyboard'],
    noarchive=False,
)


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
