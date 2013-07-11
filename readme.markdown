# minipki - Certificate authority with no privilege separation

This tool is a Python wrapper script for OpenSSL. I use it to keep track of the two tiny PKIs that I administer - one for home, and one for a client. 

It's intended for use by people who handle the whole infrastructure themselves. For me, the priviledge separation of creating a key on one host, generating a CSR, copying the CSR to the CA, signing the CSR, and copying the cert back to the host isn't very useful since I'm doing everything myself anyway.

## Requirements

- python3
    - On Unix: python3 in your path. 
    - On Windows: 
        - Python3 installed somewhere
        - The provided `minipki.bat` file. Edit it to contain the paths to python3 and minipki, and 
          then copy it anywhere you like (I recommend somewhere in your `%PATH%`).
- openssl
  - On Unix: openssl in your `$PATH`.
  - On Windows: either openssl.exe in your `%PATH%`, or one with oen of the following packages installed: [OpenVPN](http://openvpn.net/), [GnuWin32's openssl pacakge](http://gnuwin32.sourceforge.net/packages/openssl.htm), or [msysgit](https://git.wiki.kernel.org/).

## How to use

### The certificate authority

**Option 1: generate a new certificate authority**

First do this to generate your CA: 

    minipki initca \
        --ca_commonName "New mini-CA" \ 
        --organizationName "Your org"
        --emailAddress "you@example.com" \
        --countryName "US" \
        --stateOrProvinceName "TX" \
        --localityName "not sure what even goes here" \

The `--ca_commonName` argument is required, but the rest are optional. 

**Option 2: use an existing CA**

If you already have a CA, you'll need to make sure the layout is the same as I expect. 

- The CA directory
    - newcerts/
        - each signed certificate, stored as $serialnumber.pem, such as 01.pem, 02.pem, etc
    - private/
        - ca.key.pem
    - certified-keys/
        - this can be empty; it's where the new keys, certs, cnf files, and csrs for servers will be saved
    - ca.crt.pem
    - ca.openssl.cnf
        - you'll need to make sure that this hierarchy is also reflected in your ca.openssl.cnf file! 
    - index.txt
    - serial.txt

### Generating certs for servers

Once you have the CA, you can start generating server keys and certificates.

    minipki gensign servername \
        --commonName "server.example.com" \
        --subjectAltName "*.wildcard.example.com,randomcname.example.com,server,10.10.10.10"

Both `--commonName` and `--subjectAltName` are optional. The SAN list is a comma-separated list of alternative names. If the CN is not specified, minipki assumes that the servername you provide is the CN. 

The above command generates a new key and a CSR, and has the CA sign it, all in one step. You can instead accomplish this in pieces by doing the following

1. Make the configuration file for the new server

        minipki makecnf servername \
            --commonName "server.example.com" \
            --subjectAltName "*.wildcard.example.com,randomcname.example.com,server,10.10.10.10"

2. Optionally edit that file before continuing (it was saved as `certified-keys/$servername.openssl.cnf`)

3. Generate the private key for the new server:

        minipki genkey servername 

4. Sign the server certificate with the CA key

        minipki sign servername

You can even do the first three steps on the server itself, and submit the fourth step to be done by your CA, if you have separated infrastructure like that. 

### Other

I've also included the utility subcommand `minipki examinecsr`, which just runs openssl against a CSR file and returns mostly human-readable text to you. This is mostly for my own convenience, since in the process of making minipki I kept having to remember how to invoke openssl directly. 

### On subjectAltName

As you can see, the altnames stuff is optional, but I run into it a lot (and it also was the part that gave me the most trouble when I used to manage my PKIs by invoking the OpenSSL binary directly). You'll need to deal with alt names if any of the following are true:

- if the server responds to a wildcard
- if the server just has multiple domain names
- if you want to access the server by IP address as well as domain name
- if sometimes you want to use its FQDN (like <https://beerbread.example.com>) and sometimes just by its hostname (like <https://beerbread>)
- if you want to use the same cert to secure services both inside and outside of a NAT (e.g. if your internal hostname is beerbread.is.the.greatest but your external hostname is beerbread.dyndns.com)

### OpenVPN use

I use [OpenVPN](http://openvpn.net/index.php/open-source/downloads.html) for several clients as well (it's part of the excellent [pfSense](http://www.pfsense.org/), which I like a lot), and I added some functionality for dealing with OpenVPN certificate authorities as well. 

Much of the functionality is the same - you can use `minipki [genkey|gensign|buildcnf]` exactly as before. However, I added another step in the process - `minipki vpnconfig` will create an OpenVPN configuration file for an existing private client key, and `minipki vpngensign` will generate a private key, sign it, and build an OpenVPN config file all in one step. Both of these subcommands also zip up all the client configuration files - that is, `dh1025.pem`, `ca.crt.pem`, `clientname.key`, `clientname.cert`, and `vpnname.ovpn` - for easy deployment. 

(Note that this is a bit less polished than the CA use case. For example, it lacks a `vpninit` subcommand which would generate `dh1024.pem` for you. This should be fixed.)

I've also added some extra options for VPN use. When generating CSRs, you can use `--cnf` to specify a cnf file rather than have `minipki` build one for you or find one named like `keyname.openssl.cnf`. I use this because I have the same openssl.cnf file for all my OpenVPN client keys to make things simpler (and rather than using commonName or emailAddress fields to determine who a given key belongs to, I just use the filename). 

## Security

This tool was designed for PKIs for which privilege separation between server and CA make no sense, because both are handled by a single administrator. Its original intent was just to automate key generation, CSR requesting, and CSR signing. This means it can generate your private key and sign it all in one place if you wish. 

It now has developed a secondary intent, which is to insulate the user from having to know too many stupid things about OpenSSL. To this end it can automatically generate some very basic openssl.cnf files.

I haven't ever had to revoke an OpenSSL key, so it doesn't do that yet. 

## History

- First I was using openssl directly. *This way lies madness.* 
- I later turned to a makefile that came from (the apparently now defunct) sial.org. It worked pretty well, but I don't understand make's syntax, which meant that when I wanted to change it I had no idea what the fuck. 
- After a while I just pulled everything into a shell script. 
- 20111121: I wanted the script to run on Windows, so I ported it to Python and added some features. 
- 20111128: Now it's in its own local git repo, with documentation, rather than in my homedir repo
- 20111130: Name change (sslca.py -> minipki), and I'm puttin it up GitHub \m/


## License

Copyright 2011-2013 Micah R Ledbetter <mrled@younix.us>

This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. The license has been reproduced below: 

                DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                        Version 2, December 2004
    
     Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>
    
     Everyone is permitted to copy and distribute verbatim or modified
     copies of this license document, and changing it is allowed as long
     as the name is changed.
    
                DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
       TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
    
      0. You just DO WHAT THE FUCK YOU WANT TO.
