# minipki devnotes

This is where I keep information I'm likely to forget that's too long for comments in source code. 

## Server configuration

The first iteration of minipki opened your editor directly on a servername.openssl.cnf file for each server you created. 

This version just asks you what a server's main name is (probably it's FQDN), and creates the servername.openssl.cnf file automatically. 

You can still get back the old behavior if you want: 

    minipki buildconf servername
    $EDITOR servername.openssl.cnf
    minipki gencrl servername

### Basic manual editing 

- the common name of the server is specified on the `commonName` line in the config file. This is generally the FQDN and this line is required to be present. 
- If you're only *ever* going to use the commonName to access the server - that is, you'll never do https://server but always https://server.sub.domain.tld - you must remove the `subjectAltName` line, and the `[ alt_names ]` heading and the lines beneath it. This cert is only valid for what's in the commonName field, nothign else. 
- If you want to access the server other ways, including just the hostname (i.e. w/o the whole FQDN), via an IP address, or via a wildcard hostname (if *.domain.tld resolves to someserver.domain.tld), you must keep the alternative name section and specify the names that appear there. 
  - You *must* add the `commonName` as a `subjectAltName`! Yes, it has to be in there twice. It's stupid, idk. 
  - You can have as many SANs are you'd like. 
  - Here's an example `[ alt_names ]` section. 

        DNS.1 = host1.example.tld
        DNS.2 = host1
        DNS.3 = example.tld
        DNS.4 = example2.tld
        DNS.5 = *.example2.tld
        IP.1 = 10.0.0.1

## check_call vs Popen

`subprocess.check_call()` is simpler. `subprocess.Popen()` lets me specify environment variables. 

If I set the `OPENSSL_CONF` environment variable to a real openssl configuration file, it will shut the hell up about not being able to find the default one which is set at *compile time* (wtf). I've never had a `z:/strawberry_libs/build/_wrk_libs2011__.out/ssl/openssl.cnf` file on my system but please warn me about that every time I do anything!

Note that this is not the same as the `--conf` argument. Even for invocations of `openssl` which accept `--conf`, they'll still spit an error if it can't find the compiled-in configuration when the program starts. WTF.

## NSIS stuff

-   NSIS can't handle forward slashes as directory delimiters on Windows
-   AFAICT it also can't handle spaces in folder names?
