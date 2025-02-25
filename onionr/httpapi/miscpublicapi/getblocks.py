'''
    Onionr - Private P2P Communication

    Public endpoints to get block data and lists
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
from flask import Response, abort
import config
def get_public_block_list(clientAPI, publicAPI, request):
    # Provide a list of our blocks, with a date offset
    dateAdjust = request.args.get('date')
    bList = clientAPI._core.getBlockList(dateRec=dateAdjust)
    if config.get('general.hide_created_blocks', True):
        for b in publicAPI.hideBlocks:
            if b in bList:
                # Don't share blocks we created if they haven't been *uploaded* yet, makes it harder to find who created a block
                bList.remove(b)
    return Response('\n'.join(bList))

def get_block_data(clientAPI, publicAPI, data):
    '''data is the block hash in hex'''
    resp = ''
    if clientAPI._utils.validateHash(data):
        if not config.get('general.hide_created_blocks', True) or data not in publicAPI.hideBlocks:
            if data in clientAPI._core.getBlockList():
                block = clientAPI.getBlockData(data, raw=True)
                try:
                    block = block.encode() # Encode in case data is binary
                except AttributeError:
                    abort(404)
                block = clientAPI._core._utils.strToBytes(block)
                resp = block
    if len(resp) == 0:
        abort(404)
        resp = ""
    # Has to be octet stream, otherwise binary data fails hash check
    return Response(resp, mimetype='application/octet-stream')