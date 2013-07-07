#!/usr/bin/env pythyon3
# This is a wrapper script which makes these things a little easier and also generates an NSIS isntaller

import sys
import os
import subprocess
import argparse

home     = os.path.expanduser('~')
bhome    = home.replace('/','\\') #backslashes ~*~sigh~*~
#ikidir   = home+'/Documents/svn/ikiadmin'
#bikidir  = ikidir.replace('/','\\') #backslashes ~*~sigh~*~
ovpndir  = home+'/Documents/svn/ikiadmin/ssl/openvpn'
bovpndir = ovpndir.replace('/','\\') #backslashes ~*~sigh~*~

def call_minipki(keyname):
    keyname=keyname[0] #not sure why this is giving it to me as a string?
    os.chdir(ovpndir)
    #generate and sign the new key
    #subprocess.check_call([r"C:\Python32\python.exe", 
    subprocess.check_call([home+r'\opt\win32bin\minipki.bat',
                           'vpngensign', keyname,
                           '--organization', 'Neuric',
                           '--vpnserver', 'neuric.selfip.net',
                           '--cnf', bovpndir+r'\generic-client.openssl.cnf'])
def call_nsis(keyname):
    keyname=keyname[0] #not sure why this is giving it to me as a string?
    #create the installer 
    #(weird quoting is due to makensis' requirements)
    os.chdir(home) # we have to do this to use relative paths with makensis because it can't(?) handle forward-slash-separated paths
    subprocess.check_call([r"C:\Program Files (x86)\NSIS\makensis.exe",
                           r'/DOUTPUT_EXE='+bhome+r'\Downloads\Neuric-VPN-config-'+keyname+'.exe', 
                           r'/DCONFIG_CACRT='+bhome+r'\Documents\svn\ikiadmin\ssl\ca\ca.crt.pem',
                           r'/DCONFIG_ZIP='+bhome+r'\Documents\svn\ikiadmin\ssl\openvpn\certified-keys\\'+keyname+'.zip',
                           bhome+r'\Documents\svn\ikiadmin\ssl\openvpn\Neuric-OpenVPN-Config.nsi', 
                           bhome+r'\Documents\svn\ikiadmin\ssl\ca\Neuric-CA-Noheader.nsi'])


def main(*args):

    argparser = argparse.ArgumentParser(description='Make an OpenVPN key + installer without having to remember anything')
    argparser.add_argument('keyname', nargs=1, #action='store', type=str, 
                           help='Supply a keyname, usually the username or some other similar identifier.')
    argparser.add_argument('--steps', '--do', choices=['key', 'inst', 'both'], default='makeboth',
                           help='Choose which steps to perform (useful for debugging).')
    parsed = argparser.parse_args()

    if parsed.steps == 'key':
        call_minipki(parsed.keyname)
    elif parsed.steps == 'inst':
        call_nsis(parsed.keyname)
    else:
        call_minipki(parsed.keyname)
        call_nsis(parsed.keyname)
    

if __name__ == '__main__':
    sys.exit(main(*sys.argv))
