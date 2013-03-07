; This is from <http://nsis.sourceforge.net/Import_Root_Certificate>

!ifndef ___CERTIFICATE_NSH___
!define ___CERTIFICATE_NSH___
 
!include "LogicLib.nsh"
 
Var CertSize
Var CertData
 
!macro AddFirefoxCertificate CERTIFICATE PROFILE
 
  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $R0
  Push $R1
  Push $R2
  Push $R3
 
  StrCpy $0 "${CERTIFICATE}"
  StrCpy $R0 "${PROFILE}"
 
  Call AddFirefoxCertificate
 
  Pop $R3
  Pop $R2
  Pop $R1
  Pop $R0
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0
 
!macroend
 
Function AddFirefoxCertificate
 
  # read certificate
  Call __CertificateRead
 
  # find firefox
  Call __CertificateFindFirefox
 
  # set working directory for DLL files
  ${If} ${FileExists} $0
    SetOutPath $0
  ${Else}
    # alert
    MessageBox MB_OK|MB_ICONSTOP "Can't find Firefox."
    # free stuff
    Call __CertificateFree
    # bye
    Return
  ${EndIf}
 
  # add certificate
  Call __CertificateAdd
 
  # free stuff
  Call __CertificateFree
 
FunctionEnd
 
Function __CertificateFindFirefox
 
  EnumRegKey $0 HKLM "SOFTWARE\Mozilla\Mozilla Firefox" 0
  ReadRegStr $0 HKLM "SOFTWARE\Mozilla\Mozilla Firefox\$0\Main" "Install Directory"
 
FunctionEnd
 
Function __CertificateAdd
 
  # make sure certificate is read
  ${If} $CertData = 0
    MessageBox MB_OK|MB_ICONSTOP "Unable to read certificate."
    Return
  ${EndIf}
 
  # initialize password database files (secmod.db, cert8.db and key3.db)
  System::Call 'nss3::NSS_Initialize(t R0, t "", t "", t "secmod.db", i 0) i .r0'
 
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONSTOP "Password database initialization failed."
    Return
  ${EndIf}
 
  # get slot
  System::Call 'nss3::PK11_GetInternalKeySlot() i .R1'
 
  ${If} $R1 = 0
    MessageBox MB_OK|MB_ICONSTOP "Unable to get certificate slot."
    Return
  ${EndIf}
 
  # load certificate
  System::Call 'smime3::CERT_DecodeCertFromPackage(i $CertData, i $CertSize) i .R2'
 
  ${If} $R2 = 0
    MessageBox MB_OK|MB_ICONSTOP "Unable to decode certificate."
    System::Call 'nss3::PK11_FreeSlot(i R1)'
    Return
  ${EndIf}
 
  # import certificate
  System::Call 'nss3::PK11_ImportCert(i R1, i R2, i 0, i 0, i 0) i .R3'
 
  # free certificate
  System::Call 'smime3::CERT_DestroyCertificate(i R2)'
 
  # free slot
  System::Call 'nss3::PK11_FreeSlot(i R1)'
 
  # check result
  ${If} $R3 <> 0
    MessageBox MB_OK|MB_ICONSTOP "Unable to add certificate."
  ${EndIf}
 
FunctionEnd
 
!define FILE_SHARE_READ 1
!define GENERIC_READ 0x80000000
!define OPEN_EXISTING 3
!define FILE_BEGIN 0
!define FILE_END 2
!define INVALID_HANDLE_VALUE -1
!define INVALID_FILE_SIZE 0xffffffff
 
Function __CertificateRead
 
  # initialize
  Call __CertificateFree
 
  # open file
  System::Call 'kernel32::CreateFile(t r0, i ${GENERIC_READ}, \
    i ${FILE_SHARE_READ}, i 0, i ${OPEN_EXISTING}, i 0, i 0) i .r0'
 
  ${If} $0 = ${INVALID_HANDLE_VALUE}
    Return
  ${EndIf}
 
  # get file size
  System::Call 'kernel32::GetFileSize(i r0, i 0) i .r1'
 
  ${If} $1 = ${INVALID_FILE_SIZE}
    System::Call 'kernel32::CloseHandle(i r0)'
    Return
  ${EndIf}
 
  StrCpy $CertSize $1
 
  # allocate memory
  System::Alloc $1
  Pop $2
 
  ${If} $2 = 0
    System::Call 'kernel32::CloseHandle(i r0)'
    Return
  ${EndIf}
 
  # read certificate to allocated buffer
  StrCpy $3 0
  System::Call 'kernel32::ReadFile(i r0, i r2, i r1, *i .r3, i 0) i .r4'
 
  # verify results
  ${If} $4 = 0
  ${OrIf} $3 <> $1
    Call __CertificateFree
  ${Else}
    StrCpy $CertData $2
  ${EndIf}
 
  # close handle
  System::Call 'kernel32::CloseHandle(i r0)'
 
FunctionEnd
 
Function __CertificateFree
 
  ${If} $CertData <> 0
 
    System::Free $CertData
 
  ${EndIf}
 
  StrCpy $CertData ""
  StrCpy $CertSize ""
 
FunctionEnd


!define CERT_QUERY_OBJECT_FILE 1
!define CERT_QUERY_CONTENT_FLAG_ALL 16382
!define CERT_QUERY_FORMAT_FLAG_ALL 14
!define CERT_STORE_PROV_SYSTEM 10
!define CERT_STORE_OPEN_EXISTING_FLAG 0x4000
!define CERT_SYSTEM_STORE_LOCAL_MACHINE 0x20000
!define CERT_STORE_ADD_ALWAYS 4
 
Function AddCertificateToStore
 
  Exch $0
  Push $1
  Push $R0
 
  System::Call "crypt32::CryptQueryObject(i ${CERT_QUERY_OBJECT_FILE}, w r0, \
    i ${CERT_QUERY_CONTENT_FLAG_ALL}, i ${CERT_QUERY_FORMAT_FLAG_ALL}, \
    i 0, i 0, i 0, i 0, i 0, i 0, *i .r0) i .R0"
 
  ${If} $R0 <> 0
 
    System::Call "crypt32::CertOpenStore(i ${CERT_STORE_PROV_SYSTEM}, i 0, i 0, \
      i ${CERT_STORE_OPEN_EXISTING_FLAG}|${CERT_SYSTEM_STORE_LOCAL_MACHINE}, \
      w 'ROOT') i .r1"
 
    ${If} $1 <> 0
 
      System::Call "crypt32::CertAddCertificateContextToStore(i r1, i r0, \
        i ${CERT_STORE_ADD_ALWAYS}, i 0) i .R0"
      System::Call "crypt32::CertFreeCertificateContext(i r0)"
 
      ${If} $R0 = 0
 
        StrCpy $0 "Unable to add certificate to certificate store"
 
      ${Else}
 
        StrCpy $0 "success"
 
      ${EndIf}
 
      System::Call "crypt32::CertCloseStore(i r1, i 0)"
 
    ${Else}
 
      System::Call "crypt32::CertFreeCertificateContext(i r0)"
 
      StrCpy $0 "Unable to open certificate store"
 
    ${EndIf}
 
  ${Else}
 
    StrCpy $0 "Unable to open certificate file"
 
  ${EndIf}
 
  Pop $R0
  Pop $1
  Exch $0
 
FunctionEnd
 
!endif #___CERTIFICATE_NSH___
