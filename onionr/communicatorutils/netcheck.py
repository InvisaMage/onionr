'''
    Onionr - Private P2P Communication

    Determine if our node is able to use Tor based on the status of a communicator instance
    and the result of pinging onion http servers
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
import logger
from utils import netutils
def net_check(comm_inst):
    '''Check if we are connected to the internet or not when we can't connect to any peers'''
    rec = False # for detecting if we have received incoming connections recently
    if len(comm_inst.onlinePeers) == 0:
        try:
            if (comm_inst._core._utils.getEpoch() - int(comm_inst._core._utils.localCommand('/lastconnect'))) <= 60:
                comm_inst.isOnline = True
                rec = True
        except ValueError:
            pass
        if not rec and not netutils.checkNetwork(comm_inst._core._utils, torPort=comm_inst.proxyPort):
            if not comm_inst.shutdown:
                logger.warn('Network check failed, are you connected to the Internet, and is Tor working?')
            comm_inst.isOnline = False
        else:
            comm_inst.isOnline = True
    comm_inst.decrementThreadCount('net_check')