#!/usr/bin/env python3

# sslca.py
# Author: Micah R Ledbetter
# Acknowledgements: 
# - http://sial.org/howto/openssl/ca/
# - http://www.openssl.org/docs/apps/ca.html

import sys, os, shutil, argparse, logging, subprocess, socket, shutil
#logging.basicConfig(level=logging.DEBUG) #show all messages up to and including logging.debug() messages
#keysize=512 #this is for testing purposes only - weak keys, but fast generation
keysize=4096 #I prefer large keys like this. You might instead prefer 1024 or 2048.

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

    def initca(self, args):
        cacnf = "ca.openssl.cnf"

        if args.purge: #purge everything except ca.openssl.cnf
            for p in os.listdir("."): 
                if os.path.isfile(p) or os.path.islink(p): #os.unlink() handles both cases
                    os.unlink(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)
        else: #not told to purge, so if one of these exists, exit before overwriting something important
            for p in ["serial.txt", "index.txt", "private", "newcerts", "serverkeys", cacnf]:
                if (os.path.exists(p)):
                    print("Path '" + p + "' exists, exiting...")
                    sys.exit(1)

        #if not (os.path.exists(cacnf)):
        fcnf=open(cacnf,'w')
        fcnf.write(SSLCA.build_ca_cnf(self,args))
        fcnf.close()

        fserial=open("serial.txt","w")
        fserial.write("01")
        fserial.close()
        open("index.txt","w").close() #create an empty file
        os.mkdir("private",700)
        os.mkdir("newcerts",700)
        os.mkdir("serverkeys",700)

        subprocess.check_call([opensslbin, 
                               "req", #request a new key
                               "-config", cacnf,
                               "-nodes",  #"No DES", i.e. don't create an encrypted key (and don't prompt for encryption password)
                               "-x509", #puts out a self-signed cert instead of a csr; required for a CA
                               "-days", "7300", #this is about 20 years, and also the max
                               "-out", "ca.cert.pem", #will output to stdout otherwise, which we don't want
                               "-newkey", "rsa:"+str(keysize), #create an RSA key and store it where specified in cnf
                               ])

    def genprivkey(self, args):
        servername=args.servername
        logging.debug("genprivkey args: %r" % args)
        subprocess.check_call([opensslbin, "genrsa", "-out", "serverkeys/"+servername+".key", str(keysize)])
        servercnf="serverkeys/"+servername+".openssl.cnf"
        if not (os.path.exists(servercnf)):
            logging.debug("genprivkey: openssl configuration file not present, generating...")
            SSLCA.makecnf(self,args)
        subprocess.check_call([opensslbin, 
                               "req", 
                               "-new", 
                               "-nodes",
                               "-config", servercnf, 
                               "-key", "serverkeys/"+servername+".key", 
                               "-out", "serverkeys/"+servername+".csr"])

    def build_ca_cnf(self, args):
        # chunk1 is the stuff before the user settings
        # then come a few user-customizable things
        # then comes chunk2, the bulk of the file

        chunk1 ="\n"
        chunk1+="# openssl.cnf.ca\n"
        chunk1+="# Via sslca.py\n"
        chunk1+="\n"
        chunk1+="HOME                    = .\n"
        chunk1+="RANDFILE                = $ENV::HOME/.rnd\n"
        chunk1+="\n"
        chunk1+="[ root_ca_distinguished_name ]\n"

        # this is checked by argparse so we know it exists
        userchunk = "commonName = " + args.ca_commonName + "\n"
        if args.emailAddress:
            userchunk += "emailAddress = " + args.emailAddress + "\n"
        if args.countryName:
            userchunk += "countryName = " + args.countryName + "\n"
        if args.stateOrProvinceName:
            userchunk += "stateOrProvinceName = " + args.stateOrProvinceName + "\n"
        if args.localityName:
            userchunk += "localityName = " + args.localityName + "\n"
        if args.organizationName:
            userchunk += "organizationName = " + args.organizationName + "\n"

        chunk2 ="\n"
        chunk2+="[ ca ]\n"
        chunk2+="default_ca      = CA_default\n"
        chunk2+="\n"
        chunk2+="[ CA_default ]\n"
        chunk2+="dir             = .\n"
        chunk2+="#certs           = $dir/certs\n"
        chunk2+="new_certs_dir   = $dir/newcerts\n"
        chunk2+="crl_dir         = $dir/crl\n"
        chunk2+="database        = $dir/index.txt\n"
        chunk2+="\n"
        chunk2+="certificate     = $dir/ca.cert.pem\n"
        chunk2+="serial          = $dir/serial.txt\n"
        chunk2+="crl             = $dir/ca.crl.pem\n"
        chunk2+="private_key     = $dir/private/ca.key.pem\n"
        chunk2+="RANDFILE        = $dir/private/.rand\n"
        chunk2+="x509_extensions = usr_cert\n"
        chunk2+="copy_extensions	= copy\n"
        chunk2+="unique_subject  = no\n"
        chunk2+="name_opt        = ca_default\n"
        chunk2+="cert_opt        = ca_default\n"
        chunk2+="default_crl_days= 30\n"
        chunk2+="default_days    = 365\n"
        chunk2+="default_md      = sha1\n"
        chunk2+="preserve        = no\n"
        chunk2+="policy          = policy_ca\n"
        chunk2+="\n"
        chunk2+="[ policy_ca ]\n"
        chunk2+="countryName             = optional\n"
        chunk2+="stateOrProvinceName     = optional\n"
        chunk2+="organizationName        = optional\n"
        chunk2+="organizationalUnitName  = optional\n"
        chunk2+="commonName              = supplied\n"
        chunk2+="emailAddress            = optional\n"
        chunk2+="\n"
        chunk2+="[ policy_anything ]\n"
        chunk2+="countryName             = optional\n"
        chunk2+="stateOrProvinceName     = optional\n"
        chunk2+="localityName            = optional\n"
        chunk2+="organizationName        = optional\n"
        chunk2+="organizationalUnitName  = optional\n"
        chunk2+="commonName              = supplied\n"
        chunk2+="emailAddress            = optional\n"
        chunk2+="\n"
        chunk2+="[ req ]\n"
        chunk2+="default_bits            = 4096\n"
        chunk2+="default_keyfile         = ./private/ca.key.pem\n"
        chunk2+="default_md              = sha1\n"
        chunk2+="prompt                  = no\n"
        chunk2+="distinguished_name      = root_ca_distinguished_name\n"
        chunk2+="x509_extensions         = v3_ca\n"
        chunk2+="string_mask             = nombstr\n"
        chunk2+="req_extensions          = v3_req\n"
        chunk2+="\n"
        chunk2+="[ usr_cert ]\n"
        chunk2+="basicConstraints        = CA:FALSE\n"
        chunk2+="subjectKeyIdentifier    = hash\n"
        chunk2+="authorityKeyIdentifier  = keyid,issuer:always\n"
        chunk2+="\n"
        chunk2+="[ v3_req ]\n"
        chunk2+="basicConstraints        = CA:FALSE\n"
        chunk2+="keyUsage                = nonRepudiation, digitalSignature, keyEncipherment\n"
        chunk2+="\n"
        chunk2+="[ v3_ca ]\n"
        chunk2+="subjectKeyIdentifier    = hash\n"
        chunk2+="authorityKeyIdentifier  = keyid:always,issuer:always\n"
        chunk2+="basicConstraints        = CA:true\n"

        finalcnf = chunk1 + userchunk + chunk2
        return finalcnf
    
    def build_server_cnf(self, args):
        logging.debug("arguments: %r" % args)
        """Return an openssl.cnf file with the correct emailAddress field, commonName field, and optional subjectAltName section"""
        # chunk1 is the part before the commonName field
        # then comes commonName
        # then emailAddress
        # then chunk2
        # then the subjectAltName stuff, if present
        chunk1= "# server openssl configuration file\n"
        chunk1+="HOME                    = .\n"
        chunk1+="RANDFILE                = $ENV::HOME/.rnd\n"
        chunk1+="\n"
        chunk1+="[ req ]\n"
        chunk1+="default_bits            = " + str(keysize) + "\n"
        chunk1+="default_md              = sha1\n"
        chunk1+="prompt                  = no\n"
        chunk1+="string_mask             = nombstr\n"
        chunk1+="\n"
        chunk1+="distinguished_name      = req_distinguished_name\n"
        chunk1+="\n"
        chunk1+="x509_extensions         = v3_req\n"
        chunk1+="req_extensions          = v3_req\n"
        chunk1+="\n"
        chunk1+="[ req_distinguished_name ]\n"
        chunk1+="countryName = US\n"
        chunk1+="stateOrProvinceName = .\n"
        chunk1+="localityName = .\n"
        chunk1+="organizationName = .\n"

        if (args.commonname):
            cn = args.commonname
        else:
            cn = args.servername
        cnline= "commonName = " + cn + "\n"
        logging.debug("cn is %r" % cn)

        emailline= "emailAddress = " + SSLCA.emailaddress + "\n"

        chunk2= ""
        chunk2+="[ v3_req ]\n"
        chunk2+="nsCertType = server\n"
        chunk2+="basicConstraints = CA:FALSE\n"
        chunk2+="keyUsage = nonRepudiation, digitalSignature, keyEncipherment\n"

        if (args.altnames):
            # we need a separate list of ip addresses vs DNS names
            sanchunk="subjectAltName = @alt_names" + "\n\n" + "[ alt_names ]" + "\n"
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
                sanchunk += "DNS." + str(seq) + " = " + entry + '\n'
                seq+=1
            seq=1
            for entry in ip:
                sanchunk += "IP." + str(seq) + " = " + entry + '\n'
                seq+=1
        else:
            sanchunk="\n"

        servercnf = chunk1 + cnline + emailline + chunk2 + sanchunk
        #logging.debug(servercnf)
        #print(servercnf)
        return servercnf

    def printcnf(self, args):
        print(SSLCA.build_server_cnf(args))

    def makecnf(self, args):
        fcnf=open("serverkeys/"+args.servername+".openssl.cnf",'w')
        fcnf.write(SSLCA.build_server_cnf(self,args))
        fcnf.close()
        
    def signcerts(self, args):
        logging.debug("signcerts args: %r" % args)
        servername = args.servername
        subprocess.check_call([opensslbin, "ca", "-batch", "-config",
                               "ca.openssl.cnf", "-in", "serverkeys/"+servername+".csr",
                               "-out", "serverkeys/"+servername+".cert", "-days", "7300"])
    
    def gensign(self, args):
        logging.debug("gensign args: %r" % args)
        SSLCA.genprivkey(self,args)
        SSLCA.signcerts(self,args)

    def examinecsr(self, args):
        for p in [args.csrfile, args.csrfile+".csr", "serverkeys/"+args.csrfile, "serverkeys/"+args.csrfile+".csr"]:
            if os.path.exists(p):
                csrfile=p
                break
        else:
            print("No such CSR file '" + args.csrfile + "', exiting...")
            sys.exit(1)
        subprocess.check_call([opensslbin, "req", "-in", csrfile, "-noout", "-text"])

def main(*args):
    global sslca
    sslca=SSLCA()
    #logging.debug("main args: " + args)
    global opensslbin
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

    elif (os.name == 'posix'):
        # for POSIX systems we're just going to assume that openssl is in the path and $EDITOR is an existing env var. 
        inpath=which("openssl")
        if (inpath):
            opensslbin=inpath
        else:
            print("Can't find OpenSSL binary. Exiting...")
            sys.exit(1)

    argparser = argparse.ArgumentParser(description='Perform basic tasks for a mini-PKI')
    subparsers = argparser.add_subparsers()
    
    subparser_makecnf = subparsers.add_parser('makecnf', help="Generate an openssl.cnf file for a server")
    subparser_makecnf.add_argument('servername', action='store', help='Supply a servername, such as myserver or myserver.sub.domain.tld. By default, this also specifies a hostname')
    subparser_makecnf.add_argument('-c', dest='commonname', action='store', help='Specify a hostname rather than use the servername to use in the config file.')
    subparser_makecnf.add_argument('-a', dest='altnames',   action='store', help='A list of subjectAltName entries, separated by commas, such as myserver,myserver.domain.tld,10.10.10.10 .')
    subparser_makecnf.set_defaults(func=sslca.makecnf)

    subparser_examinecsr = subparsers.add_parser('examinecsr', help="Examine an existing CSR")
    subparser_examinecsr.add_argument('csrfile', action='store', help='Supply the path to a .csr file')
    subparser_examinecsr.set_defaults(func=sslca.examinecsr)

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

    subparser_initca = subparsers.add_parser('initca', help='Initialize a Certificate Authority in this directory (requires existing ca.openssl.cnf file')
    subparser_initca.add_argument('--ca_commonName', '--commonName', dest='ca_commonName',action='store', required=True, help='REQUIRED. Provide a commonName for your new CA.')
    subparser_initca.add_argument('--organizationName', action='store', help='Recommended. Provide an organization name to be included on the CA certificate and any subsequent server certificates.')
    subparser_initca.add_argument('--emailAddress', action='store', help='Recommended. Provide an email address to be included on the CA certificate and any subsequent server certificates.')
    subparser_initca.add_argument('--countryName', action='store', help='Provide a country name to be included on the CA certificate and any subsequent server certificates.')
    subparser_initca.add_argument('--stateOrProvinceName', action='store', help='Provide a state or province name to be included on the CA certificate and any subsequent server certificates.')
    subparser_initca.add_argument('--localityName', action='store', help='Provide a locality name to be included on the CA certificate and any subsequent server certificates.')
    subparser_initca.add_argument('--purge', '-p', action='store_true', help='THIS OPTION WILL DELETE ALL FILES IN THE CURRENT DIRECTORY, except for ca.openssl.cnf.')
    subparser_initca.set_defaults(func=sslca.initca)

    parsed = argparser.parse_args()
    parsed.func(parsed)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))

