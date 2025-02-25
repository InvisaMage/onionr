'''
    Onionr - Private P2P Communication

    Netcontroller library, used to control/work with Tor/I2P and send requests through them
'''
'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import subprocess, os, sys, time, signal, base64, socket
from shutil import which
import logger, config
from onionrblockapi import Block
config.reload()
def getOpenPort():
    # taken from (but modified) https://stackoverflow.com/a/2838309 by https://stackoverflow.com/users/133374/albert ccy-by-sa-3 https://creativecommons.org/licenses/by-sa/3.0/
    # changes from source: import moved to top of file, bind specifically to localhost
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

def torBinary():
    '''Return tor binary path or none if not exists'''
    torPath = './tor'
    if not os.path.exists(torPath):
        torPath = which('tor')
    return torPath

class NetController:
    '''
        This class handles hidden service setup on Tor and I2P
    '''

    def __init__(self, hsPort, apiServerIP='127.0.0.1'):
        # set data dir
        self.dataDir = os.environ.get('ONIONR_HOME', os.environ.get('DATA_DIR', 'data/'))
        if not self.dataDir.endswith('/'):
            self.dataDir += '/'

        self.torConfigLocation = self.dataDir + 'torrc'
        self.readyState = False
        self.socksPort = getOpenPort()
        self.hsPort = hsPort
        self._torInstnace = ''
        self.myID = ''
        self.apiServerIP = apiServerIP

        if os.path.exists('./tor'):
            self.torBinary = './tor'
        elif os.path.exists('/usr/bin/tor'):
            self.torBinary = '/usr/bin/tor'
        else:
            self.torBinary = 'tor'

    def generateTorrc(self):
        '''
            Generate a torrc file for our tor instance
        '''
        hsVer = '# v2 onions'
        if config.get('tor.v3onions'):
            hsVer = 'HiddenServiceVersion 3'

        if os.path.exists(self.torConfigLocation):
            os.remove(self.torConfigLocation)

        # Set the Tor control password. Meant to make it harder to manipulate our Tor instance
        plaintext = base64.b64encode(os.urandom(50)).decode()
        config.set('tor.controlpassword', plaintext, savefile=True)
        config.set('tor.socksport', self.socksPort, savefile=True)

        controlPort = getOpenPort()

        config.set('tor.controlPort', controlPort, savefile=True)

        hashedPassword = subprocess.Popen([self.torBinary, '--hash-password', plaintext], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in iter(hashedPassword.stdout.readline, b''):
            password = line.decode()
            if 'warn' not in password:
                break

        torrcData = '''SocksPort ''' + str(self.socksPort) + ''' OnionTrafficOnly
DataDirectory ''' + self.dataDir + '''tordata/
CookieAuthentication 1
ControlPort ''' + str(controlPort) + '''
HashedControlPassword ''' + str(password) + '''
        '''
        if config.get('general.security_level', 1) == 0:
            torrcData += '''\nHiddenServiceDir ''' + self.dataDir + '''hs/
\n''' + hsVer + '''\n
HiddenServicePort 80 ''' + self.apiServerIP + ''':''' + str(self.hsPort)

        torrc = open(self.torConfigLocation, 'w')
        torrc.write(torrcData)
        torrc.close()
        return

    def startTor(self):
        '''
            Start Tor with onion service on port 80 & socks proxy on random port
        '''

        self.generateTorrc()

        if os.path.exists('./tor'):
            self.torBinary = './tor'
        elif os.path.exists('/usr/bin/tor'):
            self.torBinary = '/usr/bin/tor'
        else:
            self.torBinary = 'tor'

        try:
            tor = subprocess.Popen([self.torBinary, '-f', self.torConfigLocation], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            logger.fatal("Tor was not found in your path or the Onionr directory. Please install Tor and try again.")
            sys.exit(1)
        else:
            # Test Tor Version
            torVersion = subprocess.Popen([self.torBinary, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for line in iter(torVersion.stdout.readline, b''):
                if 'Tor 0.2.' in line.decode():
                    logger.error('Tor 0.3+ required')
                    sys.exit(1)
                    break
            torVersion.kill()

        # wait for tor to get to 100% bootstrap
        try:
            for line in iter(tor.stdout.readline, b''):
                if 'bootstrapped 100' in line.decode().lower():
                    break
                elif 'opening socks listener' in line.decode().lower():
                    logger.debug(line.decode().replace('\n', ''))
            else:
                logger.fatal('Failed to start Tor. Maybe a stray instance of Tor used by Onionr is still running? This can also be a result of file permissions being too open')
                return False
        except KeyboardInterrupt:
            logger.fatal('Got keyboard interrupt. Onionr will exit soon.', timestamp = False, level = logger.LEVEL_IMPORTANT)
            return False

        logger.debug('Finished starting Tor.', timestamp=True)
        self.readyState = True

        try:
            myID = open(self.dataDir + 'hs/hostname', 'r')
            self.myID = myID.read().replace('\n', '')
            myID.close()
        except FileNotFoundError:
            self.myID = ""

        torPidFile = open(self.dataDir + 'torPid.txt', 'w')
        torPidFile.write(str(tor.pid))
        torPidFile.close()

        return True

    def killTor(self):
        '''
            Properly kill tor based on pid saved to file
        '''

        try:
            pid = open(self.dataDir + 'torPid.txt', 'r')
            pidN = pid.read()
            pid.close()
        except FileNotFoundError:
            return

        try:
            int(pidN)
        except:
            return

        try:
            try:
                os.kill(int(pidN), signal.SIGTERM)
            except PermissionError:
                # seems to happen on win 10
                pass
            os.remove(self.dataDir + 'torPid.txt')
        except ProcessLookupError:
            pass
        except FileNotFoundError:
            pass

        return
