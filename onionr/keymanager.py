'''
    Onionr - Private P2P Communication

    Load, save, and delete the user's public key pairs (does not handle peer keys)
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
import onionrcrypto
class KeyManager:
    def __init__(self, crypto):
        assert isinstance(crypto, onionrcrypto.OnionrCrypto)
        self._core = crypto._core
        self._utils = self._core._utils
        self.keyFile = crypto._keyFile
        self.crypto = crypto

    def addKey(self, pubKey=None, privKey=None):
        if type(pubKey) is type(None) and type(privKey) is type(None):
            pubKey, privKey = self.crypto.generatePubKey()
        pubKey = self.crypto._core._utils.bytesToStr(pubKey)
        privKey = self.crypto._core._utils.bytesToStr(privKey)
        try:
            if pubKey in self.getPubkeyList():
                raise ValueError('Pubkey already in list: %s' % (pubKey,))
        except FileNotFoundError:
            pass
        with open(self.keyFile, "a") as keyFile:
            keyFile.write(pubKey + ',' + privKey + '\n')
        return (pubKey, privKey)

    def removeKey(self, pubKey):
        '''Remove a key pair by pubkey'''
        keyList = self.getPubkeyList()
        keyData = ''
        try:
            keyList.remove(pubKey)
        except ValueError:
            return False
        else:
            keyData = ','.join(keyList)
            with open(self.keyFile, "w") as keyFile:
                keyFile.write(keyData)

    def getPubkeyList(self):
        '''Return a list of the user's keys'''
        keyList = []
        with open(self.keyFile, "r") as keyFile:
            keyData = keyFile.read()
        keyData = keyData.split('\n')
        for pair in keyData:
            if len(pair) > 0: keyList.append(pair.split(',')[0])
        return keyList
    
    def getPrivkey(self, pubKey):
        privKey = None
        with open(self.keyFile, "r") as keyFile:
            keyData = keyFile.read()
        for pair in keyData.split('\n'):
            if pubKey in pair:
                privKey = pair.split(',')[1]
        return privKey
    
    def changeActiveKey(self, pubKey):
        '''Change crypto.pubKey and crypto.privKey to a given key pair by specifying the public key'''
        if not pubKey in self.getPubkeyList():
            raise ValueError('That pubkey does not exist')
        self.crypto.pubKey = pubKey
        self.crypto.privKey = self.getPrivkey(pubKey)