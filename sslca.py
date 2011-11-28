#!/usr/bin/env python3

# sslca.py
# Author: Micah R Ledbetter
# Acknowledgements: 
# - http://sial.org/howto/openssl/ca/
# - http://www.openssl.org/docs/apps/ca.html

import sys, os, shutil, argparse, logging, subprocess
#logging.basicConfig(level=logging.CRITICAL) #show only logging.critical() messages
logging.basicConfig(level=logging.DEBUG) #show all messages up to and including logging.debug() messages

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

def genprivkey(args):
    logging.debug("genprivkey args: %r" % args)
    for clientname in args.clientname:
        subprocess.check_call([opensslbin, "genrsa", "-out", clientname+".key", "4096"])
        if not (os.path.exists(clientname+".openssl.cnf")):
            logging.debug("genprivkey: openssl configuration file not present, copying openssl.cnf.client-DEFAULT to %r" % clientname+".openssl.cnf")
            shutil.copy2("openssl.cnf.client-DEFAULT", clientname+".openssl.cnf")
            #input("Your editor was opened on the file %r; press return when you have finished editing this file (REQUIRED).")
            subprocess.check_call([myeditor, clientname+".openssl.cnf"])
        subprocess.check_call([opensslbin, "req", "-new", "-nodes", "-config", 
                               clientname+".openssl.cnf", "-key", 
                               clientname+".key", "-out", clientname+".csr"])

def cainit:
    ca-cnf="""# openssl.ca.cnf
#
# OpenSSL configuration file for custom Certificate Authority. Use a
# different openssl.cnf file to generate certificate signing requests;
# this one is for use only in Certificate Authority operations (csr ->
# cert, cert revocation, revocation list generation).
#
# Be sure to customize this file prior to use, e.g. the commonName and
# other options under the root_ca_distinguished_name section.
#

HOME                    = .
RANDFILE                = $ENV::HOME/.rnd

[ ca ]
default_ca      = CA_default

[ CA_default ]
dir             = .
# unsed at present, and my limited certs can be kept in current dir
#certs          = $dir/certs
new_certs_dir   = $dir/newcerts
crl_dir         = $dir/crl
database        = $dir/index

certificate     = $dir/ca-cert.pem
serial          = $dir/serial
crl             = $dir/ca-crl.pem
private_key     = $dir/private/ca-key.pem
RANDFILE        = $dir/private/.rand

x509_extensions = usr_cert

# If this isn't present, you can sign a CRL that requests SubjectAltName entries,
# but the SAN entries themselves won't come into the resulting certificate. Argh. 
copy_extensions	= copy

# Make new requests easier to sign - allow two subjects with same name
# (Or revoke the old certificate first.)
unique_subject  = no

# Comment out the following two lines for the "traditional"
# (and highly broken) format.
name_opt        = ca_default
cert_opt        = ca_default

default_crl_days= 30
default_days    = 365
# if need to be compatible with older software, use weaker md5
default_md      = sha1
# MSIE may need following set to yes?
preserve        = no

# A few difference way of specifying how similar the request should look
# For type CA, the listed attributes must be the same, and the optional
# and supplied fields are just that :-)
policy          = policy_match

# For the CA policy
[ policy_match ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

# For the 'anything' policy
# At this point in time, you must list all acceptable 'object'
# types.
[ policy_anything ]
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

####################################################################
[ req ]
default_bits            = 4096
default_keyfile         = ./private/ca-key.pem
default_md              = sha1

prompt                  = no
distinguished_name      = root_ca_distinguished_name

x509_extensions = v3_ca

# Passwords for private keys if not present they will be prompted for
# input_password = secret
# output_password = secret

# This sets a mask for permitted string types. There are several options. 
# default: PrintableString, T61String, BMPString.
# pkix   : PrintableString, BMPString.
# utf8only: only UTF8Strings.
# nombstr : PrintableString, T61String (no BMPStrings or UTF8Strings).
# MASK:XXXX a literal mask value.
# WARNING: current versions of Netscape crash on BMPStrings or UTF8Strings
# so use this option with caution!
string_mask = nombstr

# req_extensions = v3_req

[ root_ca_distinguished_name ]
commonName = Micah Reuben Ledbetter (CA)
countryName = US
#stateOrProvinceName = 
#localityName = 
organizationName = Micah Reuben Ledbetter
subjectAltName = email:vlack@vlack.com,email:mrled@mrled.org,email:mledbetter@neuric.com
subjectAltName = DNS:*.mrled.org,DNS:*.younix.us,DNS:*.vlack.com,DNS:*.vlack.ath.cx,DNS:*.vlack.cxm
emailAddress = vlack+ssl@vlack.com

[ usr_cert ]

# These extensions are added when 'ca' signs a request.

# This goes against PKIX guidelines but some CAs do it and some software
# requires this to avoid interpreting an end user certificate as a CA.

basicConstraints=CA:FALSE

# PKIX recommendations harmless if included in all certificates.
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer:always

#nsCaRevocationUrl               = https://www.sial.org/ca-crl.pem
#nsBaseUrl
#nsRevocationUrl
#nsRenewalUrl
#nsCaPolicyUrl
#nsSslServerName

[ v3_req ]

# Extensions to add to a certificate request

basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment

[ v3_ca ]


# Extensions for a typical CA

# PKIX recommendation.
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer:always

# This is what PKIX recommends but some broken software chokes on critical
# extensions.
#basicConstraints = critical,CA:true
# So we do this instead.
basicConstraints = CA:true

[ crl_ext ]

# CRL extensions.
# Only issuerAltName and authorityKeyIdentifier make any sense in a CRL.

# issuerAltName=issuer:copy
authorityKeyIdentifier=keyid:always,issuer:always
"""
    
    client-cnf="""## openssl.cnf for clients. 
## ALL YOU NEED TO CHANGE ARE THESE LINES:
## Lines for subjectAltName
## Lines for commonName
## You must add a commonName even if you're using subjectAltName entries. 
## The commonName must be a subjectAltName or some things will shit the bed

HOME                    = .
RANDFILE                = $ENV::HOME/.rnd

[ req ]
default_bits            = 4096
default_md              = sha1
prompt                  = no
string_mask             = nombstr

distinguished_name      = req_distinguished_name

x509_extensions         = v3_req
req_extensions          = v3_req

[ req_distinguished_name ]
countryName = US
stateOrProvinceName = .
localityName = .
organizationName = .
commonName = 
emailAddress = micah@micahrl.com

[ v3_req ]
nsCertType = server
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names


[ alt_names ]
DNS.1 = host1.example.tld
DNS.2 = *.example.tld
email.1 = user@example.tld
IP.1 = 10.0.0.1
"""

def signcerts(args):
    logging.debug("signcerts args: %r" % args)
    for clientname in args.clientname:
        subprocess.check_call([opensslbin, "ca", "-batch", "-config",
                               "openssl.cnf.ca", "-in", clientname+".csr",
                               "-out", clientname+".cert", "-days", "7300"])

def gensign(args):
    logging.debug("gensign args: %r" % args)
    genprivkey(args)
    signcerts(args)


def main(*args):
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
    
    subparser_genkey = subparsers.add_parser('genkey', help='Generate a private key & CRL for a server')
    subparser_genkey.add_argument('clientname', nargs='+', action='store', help='Supply a clientname, such as myserver or myserver.sub.domain.tld. The filenames for the cert, CRL, etc are based on this name. This subcommand looks for an openssl configuration file named clientname.openssl.cnf; if it does not find one, it will copy openssl.cnf.client-DEFAULT to clientname.openssl.cnf and open your editor on that file.')
    subparser_genkey.set_defaults(func=genprivkey)
    
    subparser_sign = subparsers.add_parser('sign', help='Sign a CRL with an existing CA key')
    subparser_sign.add_argument('clientname', nargs='+', action='store', help='Supply a clientname, such as myserver or myserver.sub.domain.tld. The filenames for the cert, CRL, etc are based on this name.')
    subparser_sign.set_defaults(func=signcerts)

    subparser_gensign = subparsers.add_parser('gensign', help='Both generate and sign in one step')
    subparser_gensign.add_argument('clientname', nargs='+', action='store', help='Supply a clientname, such as myserver or myserver.sub.domain.tld. The filenames for the cert, CRL, etc are based on this name. This subcommand looks for an openssl configuration file named clientname.openssl.cnf; if it does not find one, it will copy openssl.cnf.client-DEFAULT to clientname.openssl.cnf and open your editor on that file.')
    subparser_gensign.set_defaults(func=gensign)

    subparser_cainit = subparsers.add_parser('cainit', help='Initialize a mini-PKI by creating the initial configuration files and printing some help')
    subparser_cainit.set_defaults(func=cainit)
    
    parsed = argparser.parse_args()
    parsed.func(parsed)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))

