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

webpass = document.location.hash.replace('#', '')
nowebpass = false

myPub = httpGet('/getActivePubkey')

function post_to_url(path, params) {

    var form = document.createElement("form")

    form.setAttribute("method", "POST")
    form.setAttribute("action", path)

    for(var key in params) {
        var hiddenField = document.createElement("input")
        hiddenField.setAttribute("type", "hidden")
        hiddenField.setAttribute("name", key)
        hiddenField.setAttribute("value", params[key])
        form.appendChild(hiddenField)
    }

    document.body.appendChild(form)
    form.submit() 
}

if (typeof webpass == "undefined"){
    webpass = localStorage['webpass']
}
else{
    localStorage['webpass'] = webpass
    //document.location.hash = ''
}
if (typeof webpass == "undefined" || webpass == ""){
    alert('Web password was not found in memory or URL')
    nowebpass = true
}

function arrayContains(needle, arrhaystack) {
    return (arrhaystack.indexOf(needle) > -1);
}

function httpGet(theUrl) {
    var xmlHttp = new XMLHttpRequest()
    xmlHttp.open( "GET", theUrl, false ) // false for synchronous request
    xmlHttp.setRequestHeader('token', webpass)
    xmlHttp.send( null )
    if (xmlHttp.status == 200){
        return xmlHttp.responseText
    }
    else{
        return ""
    }
}
function overlay(overlayID) {
    el = document.getElementById(overlayID)
   el.style.visibility = (el.style.visibility == "visible") ? "hidden" : "visible"
   scroll(0,0)
 }

var passLinks = document.getElementsByClassName("idLink")
 for(var i = 0; i < passLinks.length; i++) {
    passLinks[i].href += '#' + webpass
 }
 
var refreshLinks = document.getElementsByClassName("refresh")

for(var i = 0; i < refreshLinks.length; i++) {
    //Can't use .reload because of webpass
    refreshLinks[i].onclick = function(){
        location.reload()
    }
}

for (var i = 0; i < document.getElementsByClassName('closeOverlay').length; i++){
    document.getElementsByClassName('closeOverlay')[i].onclick = function(e){
        document.getElementById(e.target.getAttribute('overlay')).style.visibility = 'hidden'
    }
}

var idStrings = document.getElementsByClassName('myPub')
for (var i = 0; i < idStrings.length; i++){
    if (idStrings[i].tagName.toLowerCase() == 'input'){
        idStrings[i].value = myPub
    }
    else{
        idStrings[i].innerText = myPub
    }
}