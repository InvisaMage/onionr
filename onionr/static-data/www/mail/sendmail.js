/*
    Onionr - Private P2P Communication

    This file handles the mail interface

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
*/

var sendbutton = document.getElementById('sendMail')
messageContent = document.getElementById('draftText')
to = document.getElementById('draftID')
subject = document.getElementById('draftSubject')
friendPicker = document.getElementById('friendSelect')

function sendMail(to, message, subject){
    //postData = {"postData": '{"to": "' + to + '", "message": "' + message + '"}'} // galaxy brain
    postData = {'message': message, 'to': to, 'type': 'pm', 'encrypt': true, 'meta': JSON.stringify({'subject': subject})}
    postData = JSON.stringify(postData)
    sendForm.style.display = 'none'
    fetch('/insertblock', {
        method: 'POST',
        body: postData,
        headers: {
          "content-type": "application/json",
          "token": webpass
        }})
    .then((resp) => resp.text()) // Transform the data into json
    .then(function(data) {
        sendForm.style.display = 'block'
        alert('Queued for sending!')
      })
}

var friendPicker = document.getElementById('friendSelect')
friendPicker.onchange = function(){
    to.value = friendPicker.value
}

sendForm.onsubmit = function(){
    if (friendPicker.value.trim().length !== 0 && to.value.trim().length !== 0){
        if (friendPicker.value !== to.value){
            alert('You have selected both a friend and entered a public key manually.')
            return false
        }
    }
    sendMail(to.value, messageContent.value, subject.value)
    return false
}
