!include LogicLib.nsh
!include x64.nsh
!include "NSISpcre.nsh"

!ifndef CONFIG_ZIP
    !echo "You did not pass a /DCONFIG_ZIP=C:\path\to\asdf.zip argument to makensis.exe!"
    !echo "We are assuming there is a file vpn-config.zip in the CWD."
    !define CONFIG_ZIP "vpn-config.zip"
!endif

!ifndef CONFIG_CAORG
    !echo "You did not pass a '/DCONFIG_CAORG=example' argument to makensis.exe!"
    !echo "We are calling your organization 'EXAMPLE'."
    !define CONFIG_CAORG "EXAMPLE"
!endif

!ifndef OUTPUT_EXE
    !define OUTPUT_EXE "${CONFIG_CAORG}-OpenVPN-config.exe"
!endif

Var /global OVPN_CONF_DIR
Var /global OVPNGUI_PATH
Var /global OVPN_DIR
Var /global UNINSTALLER_PATH
Var /global UNINSTALLER_KEY

!macro GetOvpnDir
    ;StrCpy $OVPN_DIR "C:\Program Files\OpenVPN"
    ;StrCpy $OVPN_CONF_DIR "$OVPN_DIR\config"

    ; If you do not do this, you will not see the 64 bit reg keys AGH.
    ${If} ${RunningX64}
        SetRegView 64
    ${EndIf}
    ClearErrors
    ReadRegStr $OVPN_DIR HKLM "SOFTWARE\OpenVPN" ""
    IfErrors 0 +3 ; iferrors, skip 0 lines, else, skip the next 2 lines (+3 means skip 2, cool right)
        MessageBox MB_OK "Cannot find OpenVPN installed. You must install OpenVPN first! Exiting..."
        Quit
    ReadRegStr $OVPN_CONF_DIR HKLM "SOFTWARE\OpenVPN" "config_dir"
    StrCpy $OVPNGUI_PATH "$OVPN_DIR\bin\openvpn-gui.exe"
    StrCpy $UNINSTALLER_PATH "$OVPN_CONF_DIR\uninstall-${CONFIG_CAORG}-vpn-config.exe"
    StrCpy $UNINSTALLER_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenVPN-${CONFIG_CAORG}-Config"
!macroend

Name "${CONFIG_CAORG} OpenVPN configuration installer"
Outfile "${OUTPUT_EXE}"
RequestExecutionLevel admin
ShowInstDetails show

Page components
Page instfiles

UninstPage instfiles

Section "${CONFIG_CAORG} OpenVPN user configuration"

    SetDetailsView show
    !insertmacro GetOvpnDir

    Setoutpath "$OVPN_CONF_DIR"
    File "/oname=${CONFIG_CAORG}-vpn-config.zip" "${CONFIG_ZIP}"
    nsUnzip::Extract /u "$OVPN_CONF_DIR\${CONFIG_CAORG}-vpn-config.zip" /d="$OVPN_CONF_DIR" /END

    ; create uninstall info
    WriteRegStr   HKLM $UNINSTALLER_KEY "DisplayName" "OpenVPN - ${CONFIG_CAORG} Configuration"
    WriteRegStr   HKLM $UNINSTALLER_KEY "UninstallString" "$UNINSTALLER_PATH"
    WriteRegStr   HKLM $UNINSTALLER_KEY "Publisher" "${CONFIG_CAORG}"
    WriteRegStr   HKLM $UNINSTALLER_KEY "NoModify" 0x1
    WriteRegDWORD HKLM $UNINSTALLER_KEY "NoRepair" 0x1
    WriteUninstaller "$UNINSTALLER_PATH"
SectionEnd

Section "Force OpenVPN to run as admin"
    SetDetailsView show
    !insertmacro GetOvpnDir
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$OVPNGUI_PATH" "RUNASADMIN"
    WriteRegStr HKCU "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$OVPNGUI_PATH" "RUNASADMIN"
SectionEnd

Section "Uninstall"
    SetDetailsView show
    !insertmacro GetOvpnDir
    DeleteRegValue HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$OVPNGUI_PATH"
    DeleteRegValue HKCU "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$OVPNGUI_PATH"
    DeleteRegKey HKLM $UNINSTALLER_KEY
    Delete /REBOOTOK "$OVPN_CONF_DIR\${CONFIG_CAORG}.ovpn"
    Delete /REBOOTOK "$OVPN_CONF_DIR\${CONFIG_CAORG}-*"
    Delete /REBOOTOK "$UNINSTALLER_PATH"
SectionEnd
