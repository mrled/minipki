# Generate a CA installer for Neuric
# This is a wrapper script so I don't have to remember NSIS cli syntax

import os, subprocess

home     = os.path.expanduser('~')
ikidir   = home+'/svn/Documents'

bhome    = home.replace('/','\\') #backslashes ~*~sigh~*~

os.chdir(home) #we have to do this to use relative paths with makensis because it can't(?) handle forward-slash-separated paths

subprocess.check_call([r"C:\Program Files\NSIS\makensis.exe",
                       r'/DOUTPUT_EXE='+bhome+r'\Downloads\Neuric-CA.exe', 
                       r'/DCONFIG_CACRT='+bhome+r'\Documents\svn\ikiadmin\ssl\ca\ca.crt.pem',
                       bhome+r'\Documents\svn\ikiadmin\ssl\ca\Neuric-CA.nsi', 
                       bhome+r'\Documents\svn\ikiadmin\ssl\ca\Neuric-CA-Noheader.nsi'])
