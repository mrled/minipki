@echo off

rem Make sure to edit this file to contain the paths to both minipki and python3

set python=C:\opt\python32\python.exe
set minipki=%USERPROFILE%\Documents\minipki\minipki

"%python%" "%minipki%" %*