; 中国象棋 (Python/PySide6) Windows 安装脚本（NSIS）
Unicode true
Name "中国象棋"
OutFile "xiangqi-pyside_0.1.0_x64-setup.exe"
InstallDir "$PROGRAMFILES64\XiangqiPySide"
RequestExecutionLevel admin

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File /r "dist-win\xiangqi-pyside\*.*"
  WriteUninstaller "$INSTDIR\uninstall.exe"
  CreateShortCut "$DESKTOP\中国象棋.lnk" "$INSTDIR\xiangqi-pyside.exe"
  CreateDirectory "$SMPROGRAMS\中国象棋"
  CreateShortCut "$SMPROGRAMS\中国象棋\中国象棋.lnk" "$INSTDIR\xiangqi-pyside.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XiangqiPySide" "DisplayName" "中国象棋 (Python/PySide6)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XiangqiPySide" "DisplayVersion" "0.1.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XiangqiPySide" "UninstallString" '"$INSTDIR\uninstall.exe"'
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\中国象棋.lnk"
  RMDir /r "$SMPROGRAMS\中国象棋"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\XiangqiPySide"
SectionEnd
