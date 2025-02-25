/*
    Onionr - Private P2P Communication

    This file loads stats to show on the main node web page

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
*/
uptimeDisplay = document.getElementById('uptime')
connectedDisplay = document.getElementById('connectedNodes')
storedBlockDisplay = document.getElementById('storedBlocks')
queuedBlockDisplay = document.getElementById('blockQueue')
lastIncoming = document.getElementById('lastIncoming')
totalRec = document.getElementById('totalRec')

function getStats(){
    stats = JSON.parse(httpGet('getstats', webpass))
    uptimeDisplay.innerText = stats['uptime'] + ' seconds'
    connectedDisplay.innerText = stats['connectedNodes']
    storedBlockDisplay.innerText = stats['blockCount']
    queuedBlockDisplay.innerText = stats['blockQueueCount']
    totalRec.innerText = httpGet('/hitcount')
    var lastConnect = httpGet('/lastconnect')
    if (lastConnect > 0){
        var humanDate = new Date(0)
        humanDate.setUTCSeconds(httpGet('/lastconnect'))
        humanDate = humanDate.toString()
        lastConnect = humanDate.substring(0, humanDate.indexOf('('));
    }
    else{
        lastConnect = 'None since start'
    }
    lastIncoming.innerText = lastConnect
}
getStats()