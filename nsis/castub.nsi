; Don't run makensis on this file directly.
; Run makensis on another .nsi file and include this one afterwards. 

!include ".\certificate.nsh"
!include LogicLib.nsh

!ifndef CONFIG_CACRT
    !echo "You did not pass a '/DCONFIG_CACRT=C:\path\to\ca.crt' argument to makensis.exe!"
    !echo "We are assuming there is a file ca.crt in the CWD."
    !define CONFIG_CACRT "ca.crt"
!endif

!ifndef CONFIG_CAORG
    !echo "You did not pass a '/DCONFIG_CAORG=example' argument to makensis.exe!"
    !echo "We are calling your organization 'EXAMPLE'."
    !define CONFIG_CAORG "EXAMPLE"
!endif

!echo "$TEMP"
Section "Install ${CONFIG_CAORG} CA"
    File '/oname="$TEMP\ca.crt"' "${CONFIG_CACRT}"

    ; Internet Explorer
    Push "$TEMP\ca.crt"
    Call AddCertificateToStore
    Pop $0
    ${If} $0 != success
        MessageBox MB_OK "import failed: $0"
    ${EndIf}

    ; Firefox
    ReadINIStr $1 "$APPDATA\Mozilla\Firefox\profiles.ini" "Profile0" "Path"
        IfErrors 0 +2 ; if errors, jump 0 lines; else jump +2 lines
        goto end ;if there was an error jump to end because Firefox isn't installed or hasn't been run on this account
    !insertmacro AddFirefoxCertificate $TEMP\ca.crt $APPDATA\Mozilla\Firefox\$1
    
    end: 
SectionEnd

