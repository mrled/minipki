; Run makensis on this file and include the Neuric-CA-noheader.nsi afterwards

!ifndef OUTPUT_EXE
    !define OUTPUT_EXE "Neuric-CA.exe"
!endif

!ifndef CONFIG_CAORG
    !echo "You did not pass a '/DCONFIG_CAORG=example' argument to makensis.exe!"
    !echo "We are calling your organization 'EXAMPLE'."
    !define CONFIG_CAORG "EXAMPLE"
!endif

Name "${CONFIG_CAORG} certificate authority installer"
Outfile "${OUTPUT_EXE}"
RequestExecutionLevel admin
ShowInstDetails nevershow

