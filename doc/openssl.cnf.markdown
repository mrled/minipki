# openssl.cnf files

This is some simple documentation for `openssl.cnf` files. It supplements the documentation that ships with openssl.

**An important thing for a newbie to understand**: you'll need to talk about two different types of .cnf files - certificate authority .cnf files, and server .cnf files. 

- Server .cnf files are specific to each different certificate you generate... that is, each server comes with its own private key, signing request, and .cnf file. These are generally pretty short and simple. 
- The CA .cnf file is used when the initial CA private key is generated, and when any server key is signed by the CA. This is longer and more complex than server .cnf files.

If you're told to add something to your openssl.cnf file, make sure you understand whether that's the file for the CA or the file for the server. 

**Layout**: Generically, these files are organized into stanzas by headers. Sometimes variables point to stanzas. Here's an example snippet from a sample `openssl.cnf`:

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
    
In this snipped, the `subjectAltName` field is populated by data from the `alt_names` stanza, which could be anywhere else in the file. 

# Enumeration of some specifica openssl.cnf options

### policy = (stanza)

A `policy =` line tells openssl which attributes (such as `countryName`, `stateOrProvince`, `organizationName`, etc) are required for a given type of certificate. 

You might have a `[ CA_default ]` stanza which provides options for CA certificates; inside that stanze you'd have a line like `policy = policy_ca`. This tells openssl to look for a separate `[ policy_ca ]` stanza which provides policy for the `[ CA_default ]` stanza, and that might look like this: 

    [ policy_ca ]
    countryName             = optional
    stateOrProvinceName     = optional
    organizationName        = optional
    organizationalUnitName  = optional
    commonName              = supplied
    emailAddress            = optional

That example makes commonName required, but everything else optional.

## copy_extensions

Set this to `copy_extensions = copy`. 
If this isn't present, you can sign a CRL that requests SubjectAltName entries,
but the SAN entries themselves won't come into the resulting certificate. Argh. 

## unique_subject

Set this to `no` - it makes new requests easier to sign because it allows two subjects with same name.

If you set this to `yes`, you must revoke the old certificate first. 

## basicConstraints 

**For non-CAs:** I set this to `CA:FALSE` for non-CA certs. This goes against PKIX guidelines but some CAs do it and some software requires this to avoid interpreting an end user certificate as a CA.

**For CAs:** The PKIX recommends `basicConstraints = critical,CA:true`, but some broken software chokes on critical so I do `basicConstraints = CA:true` instead. 


