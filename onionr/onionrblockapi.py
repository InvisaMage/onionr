'''
    Onionr - P2P Anonymous Storage Network

    This file contains the OnionrBlocks class which is a class for working with Onionr blocks
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

import core as onionrcore, logger, config, onionrexceptions, nacl.exceptions
import json, os, sys, datetime, base64, onionrstorage
from onionrusers import onionrusers

class Block:
    blockCacheOrder = list() # NEVER write your own code that writes to this!
    blockCache = dict() # should never be accessed directly, look at Block.getCache()

    def __init__(self, hash = None, core = None, type = None, content = None, expire=None, decrypt=False, bypassReplayCheck=False):
        # take from arguments
        # sometimes people input a bytes object instead of str in `hash`
        if (not hash is None) and isinstance(hash, bytes):
            hash = hash.decode()

        self.hash = hash
        self.core = core
        self.btype = type
        self.bcontent = content
        self.expire = expire
        self.bypassReplayCheck = bypassReplayCheck

        # initialize variables
        self.valid = True
        self.raw = None
        self.signed = False
        self.signature = None
        self.signedData = None
        self.blockFile = None
        self.parent = None
        self.bheader = {}
        self.bmetadata = {}
        self.isEncrypted = False
        self.decrypted = False
        self.signer = None
        self.validSig = False
        self.autoDecrypt = decrypt

        # handle arguments
        if self.getCore() is None:
            self.core = onionrcore.Core()

        self.update()

    def decrypt(self, encodedData = True):
        '''
            Decrypt a block, loading decrypted data into their vars
        '''

        if self.decrypted:
            return True
        retData = False
        core = self.getCore()
        # decrypt data
        if self.getHeader('encryptType') == 'asym':
            try:
                self.bcontent = core._crypto.pubKeyDecrypt(self.bcontent, encodedData=encodedData)
                bmeta = core._crypto.pubKeyDecrypt(self.bmetadata, encodedData=encodedData)
                try:
                    bmeta = bmeta.decode()
                except AttributeError:
                    # yet another bytes fix
                    pass
                self.bmetadata = json.loads(bmeta)
                self.signature = core._crypto.pubKeyDecrypt(self.signature, encodedData=encodedData)
                self.signer = core._crypto.pubKeyDecrypt(self.signer, encodedData=encodedData)
                self.bheader['signer'] = self.signer.decode()
                self.signedData =  json.dumps(self.bmetadata) + self.bcontent.decode()

                # Check for replay attacks
                try:
                    if self.core._utils.getEpoch() - self.core.getBlockDate(self.hash) < 60:
                        assert self.core._crypto.replayTimestampValidation(self.bmetadata['rply'])
                except (AssertionError, KeyError, TypeError) as e:
                    if not self.bypassReplayCheck:
                        # Zero out variables to prevent reading of replays
                        self.bmetadata = {}
                        self.signer = ''
                        self.bheader['signer'] = ''
                        self.signedData = ''
                        self.signature = ''
                        raise onionrexceptions.ReplayAttack('Signature is too old. possible replay attack')
                try:
                    assert self.bmetadata['forwardEnc'] is True
                except (AssertionError, KeyError) as e:
                    pass
                else:
                    try:
                        self.bcontent = onionrusers.OnionrUser(self.getCore(), self.signer).forwardDecrypt(self.bcontent)
                    except (onionrexceptions.DecryptionError, nacl.exceptions.CryptoError) as e:
                        logger.error(str(e))
                        pass
            except nacl.exceptions.CryptoError:
                pass
                #logger.debug('Could not decrypt block. Either invalid key or corrupted data')
            except onionrexceptions.ReplayAttack:
                logger.warn('%s is possibly a replay attack' % (self.hash,))
            else:
                retData = True
                self.decrypted = True
        else:
            logger.warn('symmetric decryption is not yet supported by this API')
        return retData

    def verifySig(self):
        '''
            Verify if a block's signature is signed by its claimed signer
        '''

        core = self.getCore()

        if core._crypto.edVerify(data=self.signedData, key=self.signer, sig=self.signature, encodedData=True):
            self.validSig = True
        else:
            self.validSig = False
        return self.validSig


    def update(self, data = None, file = None):
        '''
            Loads data from a block in to the current object.

            Inputs:
            - data (str):
              - if None: will load from file by hash
              - else: will load from `data` string
            - file (str):
              - if None: will load from file specified in this parameter
              - else: will load from wherever block is stored by hash

            Outputs:
            - (bool): indicates whether or not the operation was successful
        '''
        try:
            # import from string
            blockdata = data

            # import from file
            if blockdata is None:
                try:
                    blockdata = onionrstorage.getData(self.core, self.getHash()).decode()
                except AttributeError:
                    raise onionrexceptions.NoDataAvailable('Block does not exist')
            else:
                self.blockFile = None
            # parse block
            self.raw = str(blockdata)
            self.bheader = json.loads(self.getRaw()[:self.getRaw().index('\n')])
            self.bcontent = self.getRaw()[self.getRaw().index('\n') + 1:]
            if ('encryptType' in self.bheader) and (self.bheader['encryptType'] in ('asym', 'sym')):
                self.bmetadata = self.getHeader('meta', None)
                self.isEncrypted = True
            else:
                self.bmetadata = json.loads(self.getHeader('meta', None))
            self.parent = self.getMetadata('parent', None)
            self.btype = self.getMetadata('type', None)
            self.signed = ('sig' in self.getHeader() and self.getHeader('sig') != '')
            # TODO: detect if signer is hash of pubkey or not
            self.signer = self.getHeader('signer', None)
            self.signature = self.getHeader('sig', None)
            # signed data is jsonMeta + block content (no linebreak)
            self.signedData = (None if not self.isSigned() else self.getHeader('meta') + self.getContent())
            self.date = self.getCore().getBlockDate(self.getHash())
            self.claimedTime = self.getHeader('time', None)

            if not self.getDate() is None:
                self.date = datetime.datetime.fromtimestamp(self.getDate())

            self.valid = True

            if len(self.getRaw()) <= config.get('allocations.blockCache', 500000):
                self.cache()
            
            if self.autoDecrypt:
                self.decrypt()

            return True
        except Exception as e:
            logger.warn('Failed to parse block %s.' % self.getHash(), error = e, timestamp = False)

            # if block can't be parsed, it's a waste of precious space. Throw it away.
            if not self.delete():
                logger.warn('Failed to delete invalid block %s.' % self.getHash(), error = e)
            else:
                logger.debug('Deleted invalid block %s.' % self.getHash(), timestamp = False)

        self.valid = False
        return False

    def delete(self):
        '''
            Deletes the block's file and records, if they exist

            Outputs:
            - (bool): whether or not the operation was successful
        '''

        if self.exists():
            try:
                os.remove(self.getBlockFile())
            except TypeError:
                pass
            self.getCore().removeBlock(self.getHash())
            return True
        return False

    def save(self, sign = False, recreate = True):
        '''
            Saves a block to file and imports it into Onionr

            Inputs:
            - sign (bool): whether or not to sign the block before saving
            - recreate (bool): if the block already exists, whether or not to recreate the block and save under a new hash

            Outputs:
            - (bool): whether or not the operation was successful
        '''

        try:
            if self.isValid() is True:
                '''
                if (not self.getBlockFile() is None) and (recreate is True):
                    onionrstorage.store(self.core, self.getRaw().encode())
                    #with open(self.getBlockFile(), 'wb') as blockFile:
                    #    blockFile.write(self.getRaw().encode())
                else:
                '''
                self.hash = self.getCore().insertBlock(self.getRaw(), header = self.getType(), sign = sign, meta = self.getMetadata(), expire = self.getExpire())
                if self.hash != False:
                    self.update()

                return self.getHash()
            else:
                logger.warn('Not writing block; it is invalid.')
        except Exception as e:
            logger.error('Failed to save block.', error = e, timestamp = False)

        return False

    # getters

    def getExpire(self):
        '''
            Returns the expire time for a block

            Outputs:
            - (int): the expire time for a block, or None
        '''
        return self.expire

    def getHash(self):
        '''
            Returns the hash of the block if saved to file

            Outputs:
            - (str): the hash of the block, or None
        '''

        return self.hash

    def getCore(self):
        '''
            Returns the Core instance being used by the Block

            Outputs:
            - (Core): the Core instance
        '''

        return self.core

    def getType(self):
        '''
            Returns the type of the block

            Outputs:
            - (str): the type of the block
        '''
        return self.btype

    def getRaw(self):
        '''
            Returns the raw contents of the block, if saved to file

            Outputs:
            - (str): the raw contents of the block, or None
        '''

        return str(self.raw)

    def getHeader(self, key = None, default = None):
        '''
            Returns the header information

            Inputs:
            - key (str): only returns the value of the key in the header

            Outputs:
            - (dict/str): either the whole header as a dict, or one value
        '''

        if not key is None:
            if key in self.getHeader():
                return self.getHeader()[key]
            return default
        return self.bheader

    def getMetadata(self, key = None, default = None):
        '''
            Returns the metadata information

            Inputs:
            - key (str): only returns the value of the key in the metadata

            Outputs:
            - (dict/str): either the whole metadata as a dict, or one value
        '''

        if not key is None:
            if key in self.getMetadata():
                return self.getMetadata()[key]
            return default
        return self.bmetadata

    def getContent(self):
        '''
            Returns the contents of the block

            Outputs:
            - (str): the contents of the block
        '''

        return str(self.bcontent)

    def getParent(self):
        '''
            Returns the Block's parent Block, or None

            Outputs:
            - (Block): the Block's parent
        '''

        if type(self.parent) == str:
            if self.parent == self.getHash():
                self.parent = self
            elif Block.exists(self.parent):
                self.parent = Block(self.getMetadata('parent'), core = self.getCore())
            else:
                self.parent = None

        return self.parent

    def getDate(self):
        '''
            Returns the date that the block was received, if loaded from file

            Outputs:
            - (datetime): the date that the block was received
        '''

        return self.date

    def getBlockFile(self):
        '''
            Returns the location of the block file if it is saved

            Outputs:
            - (str): the location of the block file, or None
        '''

        return self.blockFile

    def isValid(self):
        '''
            Checks if the block is valid

            Outputs:
            - (bool): whether or not the block is valid
        '''

        return self.valid

    def isSigned(self):
        '''
            Checks if the block was signed

            Outputs:
            - (bool): whether or not the block is signed
        '''

        return self.signed

    def getSignature(self):
        '''
            Returns the base64-encoded signature

            Outputs:
            - (str): the signature, or None
        '''

        return self.signature

    def getSignedData(self):
        '''
            Returns the data that was signed

            Outputs:
            - (str): the data that was signed, or None
        '''

        return self.signedData

    def isSigner(self, signer, encodedData = True):
        '''
            Checks if the block was signed by the signer inputted

            Inputs:
            - signer (str): the public key of the signer to check against
            - encodedData (bool): whether or not the `signer` argument is base64 encoded

            Outputs:
            - (bool): whether or not the signer of the block is the signer inputted
        '''

        try:
            if (not self.isSigned()) or (not self.getCore()._utils.validatePubKey(signer)):
                return False

            return bool(self.getCore()._crypto.edVerify(self.getSignedData(), signer, self.getSignature(), encodedData = encodedData))
        except:
            return False

    # setters

    def setType(self, btype):
        '''
            Sets the type of the block

            Inputs:
            - btype (str): the type of block to be set to

            Outputs:
            - (Block): the Block instance
        '''

        self.btype = btype
        return self

    def setMetadata(self, key, val):
        '''
            Sets a custom metadata value

            Metadata should not store block-specific data structures.

            Inputs:
            - key (str): the key
            - val: the value (type is irrelevant)

            Outputs:
            - (Block): the Block instance
        '''

        if key == 'parent' and (not val is None) and (not val == self.getParent().getHash()):
            self.setParent(val)
        else:
            self.bmetadata[key] = val
        return self

    def setContent(self, bcontent):
        '''
            Sets the contents of the block

            Inputs:
            - bcontent (str): the contents to be set to

            Outputs:
            - (Block): the Block instance
        '''

        self.bcontent = str(bcontent)
        return self

    def setParent(self, parent):
        '''
            Sets the Block's parent

            Inputs:
            - parent (Block/str): the Block's parent, to be stored in metadata

            Outputs:
            - (Block): the Block instance
        '''

        if type(parent) == str:
            parent = Block(parent, core = self.getCore())

        self.parent = parent
        self.setMetadata('parent', (None if parent is None else self.getParent().getHash()))
        return self

    # static functions

    def getBlocks(type = None, signer = None, signed = None, parent = None, reverse = False, limit = None, core = None):
        '''
            Returns a list of Block objects based on supplied filters

            Inputs:
            - type (str): filters by block type
            - signer (str/list): filters by signer (one in the list has to be a signer)
            - signed (bool): filters out by whether or not the block is signed
            - reverse (bool): reverses the list if True
            - core (Core): lets you optionally supply a core instance so one doesn't need to be started

            Outputs:
            - (list): a list of Block objects that match the input
        '''

        try:
            core = (core if not core is None else onionrcore.Core())

            if (not parent is None) and (not isinstance(parent, Block)):
                parent = Block(hash = parent, core = core)

            relevant_blocks = list()
            blocks = (core.getBlockList() if type is None else core.getBlocksByType(type))

            for block in blocks:
                if Block.exists(block):
                    block = Block(block, core = core)

                    relevant = True

                    if (not signed is None) and (block.isSigned() != bool(signed)):
                        relevant = False
                    if not signer is None:
                        if isinstance(signer, (str,)):
                            signer = [signer]
                        if isinstance(signer, (bytes,)):
                            signer = [signer.decode()]

                        isSigner = False
                        for key in signer:
                            if block.isSigner(key):
                                isSigner = True
                                break

                        if not isSigner:
                            relevant = False

                    if not parent is None:
                        blockParent = block.getParent()

                        if blockParent is None:
                            relevant = False
                        else:
                            relevant = parent.getHash() == blockParent.getHash()

                    if relevant and (limit is None or len(relevant_Blocks) <= int(limit)):
                        relevant_blocks.append(block)

            if bool(reverse):
                relevant_blocks.reverse()

            return relevant_blocks
        except Exception as e:
            logger.debug('Failed to get blocks.', error = e)

        return list()

    def mergeChain(child, file = None, maximumFollows = 1000, core = None):
        '''
            Follows a child Block to its root parent Block, merging content

            Inputs:
            - child (str/Block): the child Block to be followed
            - file (str/file): the file to write the content to, instead of returning it
            - maximumFollows (int): the maximum number of Blocks to follow
        '''

        # validate data and instantiate Core
        core = (core if not core is None else onionrcore.Core())
        maximumFollows = max(0, maximumFollows)

        # type conversions
        if type(child) == list:
            child = child[-1]
        if type(child) == str:
            child = Block(child)
        if (not file is None) and (type(file) == str):
            file = open(file, 'ab')

        # only store hashes to avoid intensive memory usage
        blocks = [child.getHash()]

        # generate a list of parent Blocks
        while True:
            # end if the maximum number of follows has been exceeded
            if len(blocks) - 1 >= maximumFollows:
                break

            block = Block(blocks[-1], core = core).getParent()

            # end if there is no parent Block
            if block is None:
                break

            # end if the Block is pointing to a previously parsed Block
            if block.getHash() in blocks:
                break

            # end if the block is not valid
            if not block.isValid():
                break

            blocks.append(block.getHash())

        buffer = b''

        # combine block contents
        for hash in blocks:
            block = Block(hash, core = core)
            contents = block.getContent()
            contents = base64.b64decode(contents.encode())

            if file is None:
                try:
                    buffer += contents.encode()
                except AttributeError:
                    buffer += contents
            else:
                file.write(contents)
        if file is not None:
            file.close()

        return (None if not file is None else buffer)

    def exists(bHash):
        '''
            Checks if a block is saved to file or not

            Inputs:
            - hash (str/Block):
              - if (Block): check if this block is saved to file
              - if (str): check if a block by this hash is in file

            Outputs:
            - (bool): whether or not the block file exists
        '''

        # no input data? scrap it.
        if bHash is None:
            return False
        '''
        if type(hash) == Block:
            blockfile = hash.getBlockFile()
        else:
            blockfile = onionrcore.Core().dataDir + 'blocks/%s.dat' % hash
        '''
        if isinstance(bHash, Block):
            bHash = bHash.getHash()
        
        ret = isinstance(onionrstorage.getData(onionrcore.Core(), bHash), type(None))

        return not ret

    def getCache(hash = None):
        # give a list of the hashes of the cached blocks
        if hash is None:
            return list(Block.blockCache.keys())

        # if they inputted self or a Block, convert to hash
        if type(hash) == Block:
            hash = hash.getHash()

        # just to make sure someone didn't put in a bool or something lol
        hash = str(hash)

        # if it exists, return its content
        if hash in Block.getCache():
            return Block.blockCache[hash]

        return None

    def cache(block, override = False):
        # why even bother if they're giving bad data?
        if not type(block) == Block:
            return False

        # only cache if written to file
        if block.getHash() is None:
            return False

        # if it's already cached, what are we here for?
        if block.getHash() in Block.getCache() and not override:
            return False

        # dump old cached blocks if the size exceeds the maximum
        if sys.getsizeof(Block.blockCacheOrder) >= config.get('allocations.block_cache_total', 50000000): # 50MB default cache size
            del Block.blockCache[blockCacheOrder.pop(0)]

        # cache block content
        Block.blockCache[block.getHash()] = block.getRaw()
        Block.blockCacheOrder.append(block.getHash())

        return True
