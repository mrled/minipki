#!/usr/bin/env python3

# sslca.py
# Author: Micah R Ledbetter
# Acknowledgements: 
# - http://sial.org/howto/openssl/ca/
# - http://www.openssl.org/docs/apps/ca.html

import sys, os, shutil, argparse, logging, subprocess, socket
logging.basicConfig(level=logging.CRITICAL) #show only logging.critical() messages
#logging.basicConfig(level=logging.DEBUG) #show all messages up to and including logging.debug() messages

def is_exe(fpath):
    return os.path.exists(fpath) and os.access(fpath, os.X_OK)

def which(program):
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

class SSLCA:

    emailaddress="micah@micahrl.com"
    
    def genprivkey(self, args):
        servername=args.servername
        logging.debug("genprivkey args: %r" % args)
        subprocess.check_call([opensslbin, "genrsa", "-out", servername+".key", "4096"])
        configfile=servername+".openssl.cnf"
        if not (os.path.exists(configfile)):
            logging.debug("genprivkey: openssl configuration file not present, generating...")
            f=open(configfile,'w')
            print(SSLCA.build_server_cnf(self,args),file=f)
            f.close()
            #shutil.copy2("server-default.openssl.cnf", servername+".openssl.cnf")
            #print("Your editor was opened on the file %r; edit the file (REQUIRED) then close your editor to resume operation.")
            #subprocess.check_call([myeditor, servername+".openssl.cnf"])
        subprocess.check_call([opensslbin, "req", "-new", "-nodes",
                               "-config", configfile, "-key", 
                               servername+".key", "-out", servername+".csr"])
    
    def build_server_cnf(self, args):
        logging.debug("arguments: %r" % args)
        """Return an openssl.cnf file with the correct emailAddress field, commonName field, and optional subjectAltName section"""
        # chunk1 is the part before the commonName field
        # then comes commonName
        # then emailAddress
        # then chunk2
        # then the subjectAltName stuff, if present
        chunk1= "# server openssl configuration file\r\n"
        chunk1+="HOME                    = .\r\n"
        chunk1+="RANDFILE                = $ENV::HOME/.rnd\r\n"
        chunk1+="\r\n"
        chunk1+="[ req ]\r\n"
        chunk1+="default_bits            = 4096\r\n"
        chunk1+="default_md              = sha1\r\n"
        chunk1+="prompt                  = no\r\n"
        chunk1+="string_mask             = nombstr\r\n"
        chunk1+="\r\n"
        chunk1+="distinguished_name      = req_distinguished_name\r\n"
        chunk1+="\r\n"
        chunk1+="x509_extensions         = v3_req\r\n"
        chunk1+="req_extensions          = v3_req\r\n"
        chunk1+="\r\n"
        chunk1+="[ req_distinguished_name ]\r\n"
        chunk1+="countryName = US\r\n"
        chunk1+="stateOrProvinceName = .\r\n"
        chunk1+="localityName = .\r\n"
        chunk1+="organizationName = .\r\n"

        if (args.commonname):
            cn = args.commonname
        else:
            cn = args.servername
        cnline= "commonName = " + cn + "\r\n"
        logging.debug("cn is %r" % cn)

        emailline= "emailAddress = " + SSLCA.emailaddress + "\r\n"

        chunk2= ""
        chunk2+="[ v3_req ]\r\n"
        chunk2+="nsCertType = server\r\n"
        chunk2+="basicConstraints = CA:FALSE\r\n"
        chunk2+="keyUsage = nonRepudiation, digitalSignature, keyEncipherment\r\n"

        if (args.altnames):
            # we need a separate list of ip addresses vs DNS names
            sanchunk="subjectAltName = @alt_names" + "\r\n\r\n" + "[ alt_names ]" + "\r\n"
            ip=[] 
            dns=[]
            for entry in args.altnames.split(","):
                # test if this is an IP address by asking the socket module
                # NOTE: just because it's not a dotted quad doesn't mean it's not valid! 
                # "4" is a valid IP address! 
                # this is not ideal b/c openssl doesn't accept IPs that are not dotted quads. <sigh>
                # NOTE2: currently this doesn't match ipv6 addresses
                # see also <http://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python>
                try:
                    socket.inet_aton(entry)
                    ip.append(entry)
                except:
                    # assume it's a hostname if it fails the socket test
                    dns.append(entry)

            # The commonName MUST also be in the subjectAltName list; if it isn't specified there by the user, add it
            try: 
                socket.inet_aton(cn)
                # looks like cn is an IP address. check for it in the ip list
                for entry in ip:
                    if (entry == cn): 
                        break
                else:
                    ip.append(cn)
            except:
                # looks cn isn't an IP address, so assume it's a hostname. check for it in the dns list. 
                for entry in dns:
                    if (entry == cn): 
                        break
                else:
                    dns.append(cn)

            seq=1
            for entry in dns:
                sanchunk += "DNS." + str(seq) + " = " + entry + '\r\n'
                seq+=1
            seq=1
            for entry in ip:
                sanchunk += "IP." + str(seq) + " = " + entry + '\r\n'
                seq+=1
        else:
            sanchunk=""

        configfile = chunk1 + cnline + emailline + chunk2 + sanchunk
        #logging.debug(configfile)
        #print(configfile)
        return configfile

    def print_server_cnf(self, args):
        print(SSLCA.build_server_cnf(args))
        
    def signcerts(self, args):
        logging.debug("signcerts args: %r" % args)
        servername = args.servername
        subprocess.check_call([opensslbin, "ca", "-batch", "-config",
                               "ca.openssl.cnf", "-in", servername+".csr",
                               "-out", servername+".cert", "-days", "7300"])
    
    def gensign(self, args):
        logging.debug("gensign args: %r" % args)
        SSLCA.genprivkey(self,args)
        SSLCA.signcerts(self,args)
    

def main(*args):
    global sslca
    sslca=SSLCA()
    #logging.debug("main args: " + args)
    global opensslbin
    global myeditor
    if (os.name == 'nt'):
        inpath=which("openssl.exe")
        if (inpath):
            opensslbin=inpath
        else:
            # check some known locations on Windows
            for path in [r"C:\Program Files\GnuWin32\bin\openssl.exe",
                         r"C:\Program Files (x86)\GnuWin32\bin\openssl.exe",
                         r"C:\Program Files\OpenVPN\bin\openssl.exe",
                         r"C:\Program Files (x86)\OpenVPN\bin\openssl.exe",
                         r"C:\git\bin\openssl.exe"]:
                if (is_exe(path)):
                    opensslbin=path
                    break
            else:
                # if after all that we have nothing, exit
                print("Can't find OpenSSL binary. Try adding the location of openssl.exe to your PATH environment variable. Exiting...")
                sys.exit(1)
        myeditor=r"C:\Windows\system32\notepad.exe"
    elif (os.name == 'posix'):
        # for POSIX systems we're just going to assume that openssl is in the path and $EDITOR is an existing env var. 
        inpath=which("openssl")
        if (inpath):
            opensslbin=inpath
        else:
            print("Can't find OpenSSL binary. Exiting...")
            sys.exit(1)
        myeditor=os.environ['EDITOR']

    argparser = argparse.ArgumentParser(description='Perform basic tasks for a mini-PKI')
    subparsers = argparser.add_subparsers()
    
    subparser_buildcnf = subparsers.add_parser('buildcnf', help="Generate an openssl.cnf file for a server")
    subparser_buildcnf.add_argument('servername', action='store', help='Supply a servername, such as myserver or myserver.sub.domain.tld. By default, this also specifies a hostname')
    subparser_buildcnf.add_argument('-c', dest='commonname', action='store', help='Specify a hostname rather than use the servername to use in the config file.')
    subparser_buildcnf.add_argument('-a', dest='altnames',   action='store', help='A list of subjectAltName entries, separated by commas, such as myserver,myserver.domain.tld,10.10.10.10 .')
    subparser_buildcnf.set_defaults(func=sslca.build_server_cnf)

    subparser_genkey = subparsers.add_parser('genkey', help='Generate a private key & CSR for a server')
    subparser_genkey.add_argument('servername', action='store', help='Supply a servername, such as myserver or myserver.sub.domain.tld. The filenames for the cert, CSR, etc are based on this name. This subcommand also looks for an openssl configuration file named servername.openssl.cnf; if it does not find one, it will generate one for you.')
    subparser_genkey.add_argument('-c', dest='commonname', action='store', help='Specify a hostname rather than use the servername to use in the config file.')
    subparser_genkey.add_argument('-a', dest='altnames',   action='store', help='A list of subjectAltName entries, separated by commas, such as myserver,myserver.domain.tld,10.10.10.10 .')
    subparser_genkey.set_defaults(func=sslca.genprivkey)
    
    subparser_sign = subparsers.add_parser('sign', help='Sign a CSR with an existing CA key')
    subparser_sign.add_argument('servername', nargs='+', action='store', help='Supply a servername, such as myserver or myserver.sub.domain.tld. The filenames for the cert, CSR, etc are based on this name.')
    subparser_sign.set_defaults(func=sslca.signcerts)

    subparser_gensign = subparsers.add_parser('gensign', help='Both generate and sign in one step')
    subparser_gensign.add_argument('servername', action='store', help='Supply a servername, such as myserver or myserver.sub.domain.tld. The filenames for the cert, CSR, etc are based on this name. This subcommand also looks for an openssl configuration file named servername.openssl.cnf; if it does not find one, it will generate one for you.')
    subparser_gensign.add_argument('-c', dest='commonname', action='store', help='Specify a hostname rather than use the servername to use in the config file.')
    subparser_gensign.add_argument('-a', dest='altnames',   action='store', help='A list of subjectAltName entries, separated by commas, such as myserver,myserver.domain.tld,10.10.10.10 .')
    subparser_gensign.set_defaults(func=sslca.gensign)

    
    parsed = argparser.parse_args()
    parsed.func(parsed)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))

