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
    def __init__(self, user, host, password, DBG=1):
        # constructor funct
        self.user     = user
        self.host     = host
        self.password = password
        self.DBG      = DBG
        self.spId = self.connect()
    # -----------------------------------
    # @name
    #   connect()
    # -----------------------------------
    def connect(self):
        #user = 'root'
        err = ''
        # spawn pexpect session
        print("\n>>>> Open ssh session to %s \n" %self.host)
        try:
            child = pexpect.spawn('ssh -l %s %s'%(self.user, self.host))
            session = child.expect([pexpect.TIMEOUT,
    			             self.SSH_NEWKEY,
    			             self.KEY_CHANGED,
                             '[Pp]assword:.*'])
                         #\s', '[Pp]assword:'])
            if session == 0: # Timeout
                print('>>>> err = 0 (timeout)', err)
                #err = '>>>> ERROR: \n'
                #err = err + '>>>> SSH could not login. Here is what SSH said:\n'
                #err = err + '>>>> ' + child.before + child.after
                child = None
            if session == 1: # SSH does not have the public key. Just accept it.
                print('>>>> SSH does not have public key - accept it')
                child.sendline ('yes')
                child.expect ('[Pp]assword: ')
            if session == 2: # SSH Key has changed. Return Error
                print('>>>> err = 2 (SSH key has changed')
                err = '>>>> ERROR: \n'
                err = err + '>>>> SSH has changed\n'
                err = err + '>>>> ' + child.before + child.after
                child = None
                print(err)
                # Send the password
                print('>>>> Sending password to remote host')
                child.sendline(self.password)
                # Now we are either at the command prompt or
                # the SSH login process is asking for our terminal type.
                session = child.expect (['Permission denied', self.TERMINAL_PROMPT, self.COMMAND_PROMPT])
                if session == 0:
                    print('>>>> Case i = 0 after send')
                    err = '>>>> ERROR: Permission denied on host:' + self.host + '\n'
                    err = err + '>>>> ' + 'Possibly wrong password'
                    child = None
                    print(err)
                if session == 1:
                    print('>>>> Case i = 1 after send')
                    child.sendline (self.TERMINAL_TYPE)
                    child.expect (self.COMMAND_PROMPT)
        except Exception as detail:
            print('>>>> ERROR: Handling run time error..', detail)
            print('>>>> ERROR: SSH session to {} failed \n'.format(self.host))
            return None
        return child

    # -----------------------------------
    # @name
    #   formatout()
    # -----------------------------------
    def format_output(self, s):
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
        # return formatted output
        return t + out

    # -----------------------------------
    # @name
    #   run_cmd()
    # -----------------------------------
    def run_cmd(self, child, cmd, exp='0'):
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
            print('>>>> CMD: {}\n'.format(cmd))
       
            i = child.expect([pexpect.TIMEOUT, PROMPT])
            #print '>>>> RECV: ' + str(child.before) + '\n'
            s = self.format_output(str(child.before))
            print(s)
            if i == 0:
                print('>>>> ERROR: ')
                print('>>>> Running cmd timed out' + '\n')
                return (False, False)
            else:
                f.write('>>>> RECV: ' + child.before)
                return (child.before, s)
                #return s
        except pexpect.ExceptionPexpect as e:
            print('>>>> ERROR: Exception running cmd {}\n'.format(str(e)))
            return False
        # Close log file
        f.close()

    # -----------------------------------
    # @name
    #   run_scp()
    # -----------------------------------
    def run_scp(self, src, dst, key='to'):
        #if  not os.path.isfile(src):
        #    print '>>>> ERROR: Cannot find file, Quitting.. ', src
        #    return 0
        print('>>>> scp {} from local host'.format(src))
        prefix = 'root@' + self.host + ':'
        #dstpath = 'root@' + self.host + ':' + dst
	
        if key == 'to':
            # default
	        cmd = 'scp ' + src + ' ' + prefix + dst
        else:
            cmd = 'scp ' + prefix + src + ' ' + dst

        child = pexpect.spawn(cmd) 
        print('>>>> SEND: %s' %cmd)
        # expect password
        i = child.expect([pexpect.TIMEOUT, self.SSH_NEWKEY, '[Pp]assword: '])
         
        s = self.format_output(str(child.before))
        print(s)
        #print '>>>> RECV: ' + str(child.before) + str(child.after)
        if i == 0: # Timeout
            print('>>>> ERROR!')
            print('>>>> SCP could not login. Here is what SCP said: ' + \
                   str(child.before) + str(child.after))
            sys.exit (1)
        if i == 1: # SCP does not have the public key. Just accept it.
            child.sendline ('yes')
            child.expect ('[Pp]assword: ')
        # Send the password
        print('>>>> RECV: Password: \n')
        child.sendline(self.password)
        print('>>>> SEND: ******\n')
        # Wait for a while
        time.sleep(12)
        s = self.format_output(str(child.before))
        print(s)
        return True
    # -----------------------------------
    # @name
    #   disconnect(self, conn)
    # -----------------------------------
    def disconnect(self, conn):
        # this routine is just to maintain consistency with telnet
        print(">>>> Terminate SSH session")
        return 1

def testscp():

    return 1


# -----------------------------------
# Main function
# -----------------------------------
def main():
    # main func
    print('main')
    # test ssh
    host = '10.0.0.1'
    password = 'passwd'
    sn = ssh('root', host, password)
    sn.run_cmd(sn.spId, 'ls -lsa')
    # test scp - copy from local to remote
    # src = './conf/krb5.conf'
    # dst = '/tmp'
    # sn.run_scp(src, dst)
    # test scp - copy from remote to local
    # scp from remote host
    # src = '/tmp/lnx18towin113.pcap'
    # dst = './'
    # sn.run_scp(src, dst, 'from')
    # default return
    return 1


# stand-alone script
if __name__ == "__main__":
    main()


