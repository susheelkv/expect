# -----------------------------------
# @name
#   ssh.py
#
# -----------------------------------


import os
import sys
import string
import getopt
import time
import pexpect
import getpass
import socket

from datetime import datetime
from threading import Thread

# -----------------------------------
# @name
#   Class ssh
# -----------------------------------
class ssh(object):
    """
    Class: sshSession
    """
    COMMAND_PROMPT = '[>$#] '
    TERMINAL_PROMPT = r'Terminal type\?'
    TERMINAL_TYPE = 'vt100'
    SSH_NEWKEY = r'Are you sure you want to continue connecting \(yes/no\)\?'
    KEY_CHANGED = r'Host key verification failed.'
    # -----------------------------------
    # @name
    #   __init__()
    # -----------------------------------
    def __init__(self, host, password, DBG=1):
        # constructor funct
	self.host     = host
	self.password = password
	self.DBG      = DBG
        self.spId = self.connect()
    # -----------------------------------
    # @name
    #   connect()
    # -----------------------------------
    def connect(self):
	user = 'root'
	err = ''
        # spawn pexpect session
	print "\n>>>> Open ssh session to %s \n" %self.host
	try:
            child = pexpect.spawn('ssh -l %s %s'%(user, self.host))
            i = child.expect([pexpect.TIMEOUT, 
    			 self.SSH_NEWKEY,
    			 self.KEY_CHANGED,
    			 '[Pp]assword: '])
            if i == 0: # Timeout
    	        err = '>>>> ERROR: \n'
    	        err = err + '>>>> SSH could not login. Here is what SSH said:\n'
    	        err = err + '>>>> ' + child.before + child.after
    	        child = None
                print err
            if i == 1: # SSH does not have the public key. Just accept it.
                child.sendline ('yes')
                child.expect ('[Pp]assword: ')
            if i == 2: # SSH Key has changed. Return Error
    	        err = '>>>> ERROR: \n'
    	        err = err + '>>>> SSH has changed\n'
    	        err = err + '>>>> ' + child.before + child.after
    	        child = None
    	        print err
            # Send the password
            child.sendline(self.password)
            # Now we are either at the command prompt or
            # the SSH login process is asking for our terminal type.
            i = child.expect (['Permission denied', self.TERMINAL_PROMPT, self.COMMAND_PROMPT])
            if i == 0:
                err = '>>>> ERROR: Permission denied on host:' + self.host + '\n'
    	        err = err + '>>>> ' + 'Possibly wrong password'
    	        child = None
    	        print err
            if i == 1:
                child.sendline (self.TERMINAL_TYPE)
                child.expect (self.COMMAND_PROMPT)
	except Exception:
            print '>>>> ERROR: SSH session to %s failed \n' %self.host
	    return None
        return child

    # -----------------------------------
    # @name
    #   formatout()
    # -----------------------------------
    def formatout(self, s):
        # format out
	t = ">>>> RECV: \n"
	lines = s.split('\r\n')
	lines.remove(lines[0])
	if lines:
	    last = lines[-1]
	    lines.remove(last)
	out = ""
	for l in lines:
	    tmp = ""
	    tmp = ">>>> " + str(l) + "\n"
	    out = out + tmp

	return t + out

    # -----------------------------------
    # @name
    #   runcmd()
    # -----------------------------------
    def runcmd(self, child, cmd, exp='0'):
        # Execute command
	if child == None:
            return None
        child.before = ''
        child.after = ''
        if exp == '0':
            PROMPT = self.COMMAND_PROMPT
        else:
            PROMPT = exp
    
        f = open ('ssh.out', 'a')
        try:
            child.sendline(cmd)
            print '>>>> CMD: %s\n' %cmd 
       
            i = child.expect([pexpect.TIMEOUT, PROMPT])
	    #print '>>>> RECV: ' + str(child.before) + '\n'
	    s = self.formatout(str(child.before))
	    print s
            if i == 0:
                print '>>>> ERROR:'
                print '>>>> Running cmd timed out' + '\n'
                return (False, False)
            else:
		f.write('>>>> RECV: ' + child.before)
                return (child.before, s)
		#return s
        except pexpect.ExceptionPexpect, e:
            print '>>>> ERROR: Exception running cmd %s\n' %(str(e))
            return False
        # Close log file
        f.close()

    # -----------------------------------
    # @name
    #   doscp()
    # -----------------------------------
    def doscp(self, src, dst, key='to'):
        #if  not os.path.isfile(src):
        #    print '>>>> ERROR: Cannot find file, Quitting.. ', src
        #    return 0
	print '>>>> scp %s from local host' %src
	prefix = 'root@' + self.host + ':'
	#dstpath = 'root@' + self.host + ':' + dst
	
	if key == 'to':
            # default
	    cmd = 'scp ' + src + ' ' + prefix + dst
        else:
            cmd = 'scp ' + prefix + src + ' ' + dst

        child = pexpect.spawn(cmd) 
        print '>>>> SEND: %s' %cmd
	# expect password
	i = child.expect([pexpect.TIMEOUT, self.SSH_NEWKEY, '[Pp]assword: '])
         
	s = self.formatout(str(child.before))
	print s
	#print '>>>> RECV: ' + str(child.before) + str(child.after)
        if i == 0: # Timeout
            print '>>>> ERROR!'
            print '>>>> SCP could not login. Here is what SCP said: ' + \
                   str(child.before) + str(child.after)
            sys.exit (1)
        if i == 1: # SCP does not have the public key. Just accept it.
            child.sendline ('yes')
            child.expect ('[Pp]assword: ')
        # Send the password
	print '>>>> RECV: Password: \n'
        child.sendline(self.password)
        print '>>>> SEND: ******\n'
        # Wait for a while
        time.sleep(12)
	s = self.formatout(str(child.before))
	print s

	return True
    # -----------------------------------
    # @name
    #   disconnect(self, conn)
    # -----------------------------------
    def disconnect(self, conn):
        # this routine is just to 
	# maintain consistency with telnet
	print ""
	print ">>>> Terminate SSH session\n"

        return 1


# -----------------------------------
# Main function
# -----------------------------------
def main():
    # main func
    host = '172.19.208.161'
    password = 'netapp'
    sn = ssh(host, password)
    sn.runcmd(sn.spId, 'ls -lsa')
 
    # test the new doscp func
    #src = './conf/krb5.conf'
    #dst = '/tmp'
    #sn.doscp(src, dst)

    # scp from remote host
    #src = '/tmp/lnx18towin113.pcap'
    #dst = './'
    #sn.doscp(src, dst, 'from')

    return 1

# -----------------------------------
# Main script
# -----------------------------------
if __name__ == "__main__":
    main()


